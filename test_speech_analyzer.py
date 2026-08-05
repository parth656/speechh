import sys
import types
import unittest

# These unit tests only exercise the pure review logic; they do not download or
# load a Whisper model.
sys.modules.setdefault("faster_whisper", types.SimpleNamespace(WhisperModel=object))

from practice_generator import (
    focus_words_from_profile,
    generate_adaptive_passage,
    generate_practice_content,
    generate_random_passage,
)
from speech_analyzer import MAX_REFERENCE_WORDS, SpeechAnalyzer, tokenize


def word(value, confidence=0.9):
    return {
        "word": value,
        "display_word": value,
        "start": 0.0,
        "end": 0.1,
        "confidence": confidence,
    }


class SpeechAnalyzerTests(unittest.TestCase):
    def test_transcription_is_not_primed_with_reference_text(self):
        class FakeModel:
            def transcribe(self, _audio_path, **options):
                self.options = options
                return [], types.SimpleNamespace(language="en", language_probability=1.0)

        analyzer = SpeechAnalyzer.__new__(SpeechAnalyzer)
        analyzer.model = FakeModel()
        analyzer.transcribe("recording.wav", language="en")
        self.assertEqual(analyzer.model.options["language"], "en")
        self.assertNotIn("initial_prompt", analyzer.model.options)

    def test_tokenize_normalizes_punctuation(self):
        self.assertEqual(tokenize("Hello, WORLD! It's me."), ["hello", "world", "it's", "me"])

    def test_alignment_finds_missing_and_extra_words(self):
        rows = SpeechAnalyzer.align("red blue", [word("red"), word("green")])
        self.assertEqual(rows[0][2], "match")
        self.assertEqual(rows[1][0], "blue")
        self.assertEqual(rows[1][2], "different")

    def test_every_reference_word_receives_a_correct_or_wrong_result(self):
        reviews, unexpected = SpeechAnalyzer.evaluate_reference_words(
            "The bright blue bird",
            [word("the"), word("bright"), word("green"), word("bird")],
        )
        self.assertEqual([item["expected"] for item in reviews], [
            "the", "bright", "blue", "bird"
        ])
        self.assertEqual(
            [item["status"] for item in reviews],
            ["correct", "correct", "wrong", "correct"],
        )
        self.assertEqual(reviews[2]["heard"], "green")
        self.assertEqual(unexpected, [])

    def test_missing_reference_word_is_marked_wrong(self):
        reviews, _ = SpeechAnalyzer.evaluate_reference_words(
            "red blue green", [word("red"), word("green")]
        )
        self.assertEqual(reviews[1]["expected"], "blue")
        self.assertEqual(reviews[1]["status"], "wrong")
        self.assertEqual(reviews[1]["heard"], "Not detected")

    def test_unexpected_transcript_word_is_reported(self):
        _reviews, unexpected = SpeechAnalyzer.evaluate_reference_words(
            "red blue", [word("red"), word("green"), word("blue")]
        )
        self.assertEqual([item["word"] for item in unexpected], ["green"])

    def test_reference_limit_is_enforced(self):
        reference = "word " * (MAX_REFERENCE_WORDS + 1)
        with self.assertRaises(ValueError):
            SpeechAnalyzer.align(reference, [])

    def test_low_confidence_free_speech_is_reviewed_once(self):
        findings = SpeechAnalyzer.review_free_speech(
            [word("difficult", 0.2), word("difficult", 0.1), word("the", 0.1)],
            threshold=0.55,
            maximum=10,
        )
        self.assertEqual([item["word"] for item in findings], ["difficult"])


class PracticeGeneratorTests(unittest.TestCase):
    def test_adaptive_passage_includes_focus_words(self):
        passage = generate_adaptive_passage("beginner", ["rhythm", "clarity"])
        self.assertIn("rhythm", passage)
        self.assertIn("clarity", passage)

    def test_random_passage_is_available_for_every_level(self):
        for level in ("beginner", "intermediate", "advanced"):
            passage = generate_random_passage(level)
            self.assertGreater(len(passage.split()), 10)
            self.assertEqual(len(passage.split(". ")), 3)

    def test_generated_practice_contains_each_target(self):
        text = generate_practice_content(
            ["rhythm", "comfortable"], "beginner", 4, "paragraph"
        )
        self.assertIn("rhythm", text)
        self.assertIn("comfortable", text)
        self.assertNotIn("\n", text)

    def test_profile_prioritizes_repeated_review_words(self):
        profile = {
            "clear": {"review_count": 1},
            "rhythm": {"review_count": 3},
            "ignored": {"review_count": 0},
        }
        self.assertEqual(focus_words_from_profile(profile), ["rhythm", "clear"])


if __name__ == "__main__":
    unittest.main()
