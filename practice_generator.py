import random


def generate_practice_content(wrong_words: list[str], level: str, sentences: int) -> str:
    """Create personalized practice locally, without an API or internet connection."""
    words = [word.strip().lower() for word in wrong_words if word.strip()]
    words = list(dict.fromkeys(words))[:10]
    if not words:
        raise ValueError("Complete one analysis first so the app can learn your difficult words.")

    sentences = max(3, int(sentences))
    joined = ", ".join(words[:-1]) + (f" and {words[-1]}" if len(words) > 1 else words[0])

    level_templates = {
        "beginner": [
            "Say {words} slowly and clearly.",
            "I can say {words} with confidence.",
            "Today I will practise {words} again.",
            "Listen carefully as I repeat {words}.",
            "I speak slowly when I say {words}.",
        ],
        "intermediate": [
            "I practise {words} carefully so that every sound remains clear.",
            "During today's speaking exercise, I will repeat {words} with confidence.",
            "Clear pronunciation helps me say {words} at a natural speed.",
            "I pause, breathe, and then pronounce {words} accurately.",
            "My goal is to use {words} smoothly in everyday speech.",
        ],
        "advanced": [
            "With controlled pacing and precise articulation, I confidently pronounce {words}.",
            "Consistent practice allows me to use {words} naturally in fluent conversation.",
            "I focus on each sound while repeating {words} at a comfortable speaking rate.",
            "By maintaining clarity and rhythm, I can accurately articulate {words}.",
            "I deliberately practise {words} until their pronunciation becomes effortless.",
        ],
    }

    templates = level_templates.get(level, level_templates["beginner"])
    # Give varied output while ensuring every focus word occurs in every sentence.
    selected = [templates[i % len(templates)] for i in range(sentences)]
    if sentences > len(templates):
        random.shuffle(selected)
    return "\n".join(template.format(words=joined) for template in selected)
