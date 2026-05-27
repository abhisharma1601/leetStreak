import random

_MESSAGES: dict[str, list[str]] = {
    "zero": [
        "Fresh start today. Just one question stands between you and a new streak.",
        "Day zero. The streak doesn't build itself — one problem, right now.",
        "Clean slate. Five minutes is all it takes to start something you'll be proud of.",
    ],
    "early": [
        "Day {n}. Don't kill the momentum.",
        "Day {n}. The hardest part is already behind you — just keep going.",
        "Day {n} in. One question a day is all it takes. Don't stop now.",
    ],
    "week": [
        "You're {n} days in. The first {n} days were the hardest — coast on the discipline you've already built.",
        "{n} days. You've got a real streak now. Skip today and you'll spend a week regretting it.",
        "{n} days running. That took real effort to build. One lazy evening isn't worth throwing it away.",
    ],
    "month": [
        "{n} days. That's not a streak anymore, that's a habit. Don't let one lazy evening reset it.",
        "{n} days. You've outlasted most people who ever 'started LeetCode'. Finish the question.",
        "{n} days strong. At this point skipping would feel worse than just doing it. Do it.",
    ],
    "century": [
        "{n} days. You'd really watch it all burn over a single problem?",
        "{n} days of discipline. One problem. You've done harder things in the last week alone.",
        "{n} days. This is who you are now. Open the tab and finish it.",
    ],
}


def pick(current_streak: int) -> str:
    if current_streak == 0:
        return random.choice(_MESSAGES["zero"])

    if current_streak < 7:
        template = random.choice(_MESSAGES["early"])
    elif current_streak < 30:
        template = random.choice(_MESSAGES["week"])
    elif current_streak < 100:
        template = random.choice(_MESSAGES["month"])
    else:
        template = random.choice(_MESSAGES["century"])

    return template.format(n=current_streak)
