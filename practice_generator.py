import random


PASSAGE_PARTS = {
    "beginner": {
        "openers": [
            "The morning breeze moves softly through the trees.",
            "A bright bird sings near my open window.",
            "After breakfast, I look at the sky and smile.",
            "The quiet street becomes busy as the day begins.",
            "Warm sunlight reaches the floor beside my chair.",
            "I begin the day with a calm and steady breath.",
        ],
        "actions": [
            "I choose one small task and finish it carefully.",
            "I walk to the park and notice the green leaves.",
            "I make a simple meal and share it with my family.",
            "I read a short story and imagine a new place.",
            "I tidy my desk before I start my work.",
            "I call a friend and listen to their news.",
        ],
        "closers": [
            "A peaceful moment helps me feel ready for tomorrow.",
            "By evening, I feel proud of my small progress.",
            "The fresh air makes my thoughts feel clear.",
            "I end the day slowly and get ready to rest.",
            "Each simple step helps me build confidence.",
            "I am grateful for a calm and useful day.",
        ],
    },
    "intermediate": {
        "openers": [
            "On Saturday morning, I visited a lively market near my home.",
            "A short walk through the neighbourhood gave me time to think.",
            "Learning a new skill becomes easier when I practise in small steps.",
            "During my commute, I noticed how quickly the weather changed.",
            "A thoughtful conversation can change the direction of an ordinary day.",
            "I started the week by writing down one realistic goal.",
        ],
        "actions": [
            "I compared several options before making a careful decision.",
            "I paused, reviewed my work, and adjusted my plan.",
            "I asked a useful question instead of guessing the answer.",
            "I focused on one priority before moving to the next task.",
            "I noticed a difficult detail and practised it again at a slower pace.",
            "I shared an idea with a friend and listened to a different perspective.",
        ],
        "closers": [
            "That small effort made the rest of the day feel more manageable.",
            "Regular practice helps progress become easier to notice over time.",
            "A clear plan gave me more confidence for the next step.",
            "I finished with a better understanding than I had at the start.",
            "The experience reminded me that patience produces useful results.",
            "By slowing down, I made room for a more thoughtful response.",
        ],
    },
    "advanced": {
        "openers": [
            "Effective communication depends on both clear expression and careful listening.",
            "A challenging project becomes less intimidating when its purpose is well defined.",
            "Curiosity encourages people to examine familiar problems from unfamiliar angles.",
            "A quiet moment of reflection can improve the quality of a difficult decision.",
            "Meaningful progress often begins with an honest assessment of the present situation.",
            "A productive discussion requires participants to balance confidence with openness.",
        ],
        "actions": [
            "I separated the larger goal into deliberate steps and reviewed each one.",
            "I paused between ideas so that my explanation remained precise and easy to follow.",
            "I considered evidence that challenged my first assumption before responding.",
            "I adjusted my pace, clarified the important details, and invited useful feedback.",
            "I chose specific language rather than relying on vague or repetitive phrases.",
            "I compared several possible solutions before selecting the most practical approach.",
        ],
        "closers": [
            "The result was a clearer plan and a stronger sense of responsibility.",
            "This approach made the next conversation more focused and constructive.",
            "Over time, deliberate practice transforms uncertainty into confidence.",
            "The experience showed that precision and patience can work together.",
            "A measured response often creates more progress than a quick reaction.",
            "That reflection provided a useful foundation for future improvement.",
        ],
    },
}


def generate_random_passage(level: str) -> str:
    """Create a varied, level-appropriate passage without an API or model download."""
    parts = PASSAGE_PARTS.get(level, PASSAGE_PARTS["beginner"])
    # One distinct sentence from each group gives 216 combinations per level
    # while keeping the passage coherent and free of repeated sentences.
    return " ".join(
        random.choice(parts[group]) for group in ("openers", "actions", "closers")
    )


def generate_adaptive_passage(level: str, focus_words: list[str]) -> str:
    """Create fresh reading material and add a concise, personalised drill."""
    passage = generate_random_passage(level)
    words = [word.strip().lower() for word in focus_words if word.strip()][:3]
    if not words:
        return passage
    joined = ", ".join(words[:-1]) + (f" and {words[-1]}" if len(words) > 1 else words[0])
    drills = [
        f"For focused practice, I say {joined} slowly, clearly, and then at a natural pace.",
        f"Before I finish, I repeat {joined} with steady rhythm and careful attention.",
        f"I use {joined} in a clear voice and pause briefly between each important word.",
    ]
    return f"{passage} {random.choice(drills)}"


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
