import random


RANDOM_PASSAGES = {
    "beginner": [
        "The morning sun shines through my window. I make a warm drink and plan my day. Then I take a slow walk through the quiet park.",
        "My small garden has green plants and bright flowers. I water them each morning and watch the birds near the fence. The fresh air makes me feel calm.",
        "I enjoy reading a short story after dinner. The characters travel to new places and solve simple problems. A good story helps me relax.",
    ],
    "intermediate": [
        "On Saturday, I visited a local market with a friend. We compared fresh fruit, chose a few ingredients, and cooked a simple meal at home. The conversation made the afternoon pass quickly.",
        "Learning a new skill takes patience and regular practice. I set a small goal, notice what feels difficult, and try again the next day. Progress becomes easier to see over time.",
        "During my commute, I pay attention to the changing weather and the people around me. A brief pause helps me arrive with a clearer mind and a better plan for the day.",
    ],
    "advanced": [
        "Effective communication combines clear pronunciation with thoughtful pacing. When I pause between ideas, I give listeners time to understand my meaning and give myself time to choose precise words.",
        "A challenging task often becomes manageable when it is divided into small, deliberate steps. By reviewing each attempt and adjusting my approach, I build confidence without rushing the process.",
        "Curiosity encourages me to ask better questions and consider unfamiliar perspectives. Even a brief conversation can reveal useful details, strengthen understanding, and inspire a more creative solution.",
    ],
}


def generate_random_passage(level: str) -> str:
    """Return a ready-to-read passage without requiring focus words or an API."""
    passages = RANDOM_PASSAGES.get(level, RANDOM_PASSAGES["beginner"])
    return random.choice(passages)


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
