import re
from difflib import SequenceMatcher

from faster_whisper import WhisperModel

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by",
    "for", "from", "had", "has", "have", "he", "her", "him", "his",
    "i", "if", "in", "into", "is", "it", "its", "me", "my", "of",
    "on", "or", "our", "she", "so", "that", "the", "their", "them",
    "there", "these", "they", "this", "those", "to", "was", "we",
    "were", "with", "you", "your",
}


def normalize_word(value: str) -> str:
    return re.sub(r"[^a-z0-9']", "", value.lower())


def tokenize(value: str) -> list[str]:
    return [word for word in (normalize_word(x) for x in value.split()) if word]


class SpeechAnalyzer:
    def __init__(self, model_name: str = "small.en"):
        self.model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            cpu_threads=2,
            num_workers=1,
        )

    def transcribe(self, audio_path: str, prompt: str = "") -> dict:
        segments, info = self.model.transcribe(
            audio_path,
            language="en",
            task="transcribe",
            beam_size=3,
            temperature=0.0,
            initial_prompt=prompt or None,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )

        text_parts = []
        words = []
        duration = 0.0

        for segment in segments:
            if segment.text:
                text_parts.append(segment.text.strip())
            duration = max(duration, float(segment.end or 0.0))

            for token in segment.words or []:
                clean = normalize_word(token.word)
                if clean:
                    words.append({
                        "word": clean,
                        "display_word": token.word.strip(),
                        "start": float(token.start or 0.0),
                        "end": float(token.end or 0.0),
                        "confidence": max(0.0, min(1.0, float(token.probability or 0.0))),
                    })

        return {
            "text": " ".join(text_parts).strip(),
            "words": words,
            "duration": duration,
            "language": getattr(info, "language", "en"),
            "language_probability": max(
                0.0,
                min(1.0, float(getattr(info, "language_probability", 0.0))),
            ),
        }

    @staticmethod
    def align(reference: str, recognized: list[dict]) -> list[tuple]:
        expected = tokenize(reference)
        actual = [item["word"] for item in recognized]
        rows, cols = len(expected), len(actual)
        dp = [[0] * (cols + 1) for _ in range(rows + 1)]

        for i in range(rows + 1):
            dp[i][0] = i
        for j in range(cols + 1):
            dp[0][j] = j

        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                cost = 0 if expected[i - 1] == actual[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost,
                )

        result = []
        i, j = rows, cols
        while i > 0 or j > 0:
            if i > 0 and j > 0:
                cost = 0 if expected[i - 1] == actual[j - 1] else 1
                if dp[i][j] == dp[i - 1][j - 1] + cost:
                    operation = "match" if cost == 0 else "different"
                    result.append((expected[i - 1], recognized[j - 1], operation))
                    i -= 1
                    j -= 1
                    continue
            if i > 0 and dp[i][j] == dp[i - 1][j] + 1:
                result.append((expected[i - 1], None, "missing"))
                i -= 1
            else:
                result.append((None, recognized[j - 1], "extra"))
                j -= 1

        result.reverse()
        return result

    def review_reference(
        self,
        reference: str,
        recognized: list[dict],
        threshold: float,
        maximum: int,
    ) -> list[dict]:
        findings = []

        for expected, actual, operation in self.align(reference, recognized):
            if operation == "match":
                continue

            if operation == "missing":
                if expected in STOP_WORDS:
                    continue
                findings.append({
                    "word": expected,
                    "expected": expected,
                    "heard": "Not detected",
                    "confidence": 0.0,
                    "reason": "Expected content word was not detected.",
                    "severity": 1.0,
                })
                continue

            if operation == "extra":
                if actual["word"] in STOP_WORDS or len(actual["word"]) < 3:
                    continue
                findings.append({
                    **actual,
                    "expected": "Not expected",
                    "heard": actual["display_word"],
                    "reason": "Unexpected content word was recognized.",
                    "severity": 0.65,
                })
                continue

            similarity = SequenceMatcher(None, expected, actual["word"]).ratio()
            if similarity >= 0.88 and actual["confidence"] >= threshold:
                continue
            if expected in STOP_WORDS and similarity >= 0.55:
                continue

            findings.append({
                **actual,
                "word": expected,
                "expected": expected,
                "heard": actual["display_word"],
                "reason": "A different word was recognized.",
                "severity": max(1.0 - similarity, 1.0 - actual["confidence"]),
            })

        findings.sort(key=lambda item: -item["severity"])
        return findings[:maximum]

    @staticmethod
    def review_free_speech(
        words: list[dict],
        threshold: float,
        maximum: int,
    ) -> list[dict]:
        findings = []
        seen = set()

        for item in words:
            word = item["word"]
            if word in STOP_WORDS or len(word) < 4 or word.isdigit() or word in seen:
                continue
            if item["confidence"] >= threshold:
                continue
            seen.add(word)
            findings.append({
                **item,
                "reason": "Low recognition confidence.",
                "severity": 1.0 - item["confidence"],
            })

        findings.sort(key=lambda item: item["confidence"])
        return findings[:maximum]

    def analyze(
        self,
        audio_path: str,
        mode: str,
        reference: str,
        threshold: float,
        maximum: int,
    ) -> dict:
        raw = self.transcribe(audio_path, prompt=reference)

        if mode == "Read a reference passage":
            flagged = self.review_reference(
                reference, raw["words"], threshold, maximum
            )
        else:
            flagged = self.review_free_speech(raw["words"], threshold, maximum)

        word_count = len(raw["words"])
        duration = raw["duration"]
        return {
            "mode": mode,
            "text": raw["text"],
            "duration": duration,
            "word_count": word_count,
            "words_per_minute": word_count * 60.0 / duration if duration else 0.0,
            "language": raw["language"],
            "language_probability": raw["language_probability"],
            "flagged_words": flagged,
        }
