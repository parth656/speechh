import random


def focus_words_from_profile(profile: dict[str, dict], limit: int = 6) -> list[str]:
    """Return the words that most often need review in this browser session."""
    ranked = sorted(
        profile.items(),
        key=lambda item: (-item[1].get("review_count", 0), item[0]),
    )
    return [word for word, data in ranked if data.get("review_count", 0) > 0][:limit]


def generate_practice_content(
    wrong_words: list[str], level: str, sentences: int, style: str = "sentences"
) -> str:
    """Create personalized practice locally, without an API or internet connection."""
    words = [word.strip().lower() for word in wrong_words if word.strip()]
    words = list(dict.fromkeys(words))[:10]
    if not words:
        raise ValueError("Complete one analysis first so the app can learn your difficult words.")

    sentences = max(3, int(sentences))
    level_templates = {
        "beginner": [
            "I say {word} slowly and clearly.",
            "I can say {word} with confidence.",
            "Today I will practise {word} again.",
            "I listen carefully as I repeat {word}.",
            "I speak slowly when I say {word}.",
        ],
        "intermediate": [
            "I practise {word} carefully so that every sound remains clear.",
            "During today's speaking exercise, I repeat {word} with confidence.",
            "Clear pacing helps me say {word} at a natural speed.",
            "I pause, breathe, and then say {word} accurately.",
            "My goal is to use {word} smoothly in everyday speech.",
        ],
        "advanced": [
            "With controlled pacing, I confidently say {word} in a full sentence.",
            "Consistent practice helps me use {word} naturally in conversation.",
            "I focus on each sound while repeating {word} at a comfortable pace.",
            "With clarity and rhythm, I can say {word} accurately.",
            "I deliberately practise {word} until it becomes more comfortable.",
        ],
    }

    templates = level_templates.get(level, level_templates["beginner"])
    # Rotate through targets so every focus word is practised without producing
    # unnatural sentences that contain every target at once.
    selected = [templates[i % len(templates)] for i in range(sentences)]
    if sentences > len(templates):
        random.shuffle(selected)
    content = [template.format(word=words[i % len(words)]) for i, template in enumerate(selected)]
    if style == "paragraph":
        return " ".join(content)
    return "\n".join(content)
