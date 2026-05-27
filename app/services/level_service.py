LEVELS = [
    (0, "Script Kiddie 🐣"),
    (50, "Code Monkey 🐒"),
    (150, "Algorithm Apprentice 📚"),
    (400, "DP Disciple 🧠"),
    (800, "Graph Wizard 🧙"),
    (1500, "Big-O Sensei 🥋"),
]


def level_for_points(points: int) -> tuple[str, int | None, str | None]:
    """Returns (current_level_name, next_threshold, next_level_name).
    next_threshold and next_level_name are None at max level.
    """
    current_name = LEVELS[0][1]
    for threshold, name in LEVELS:
        if points >= threshold:
            current_name = name
        else:
            break

    for i, (threshold, name) in enumerate(LEVELS):
        if name == current_name and i + 1 < len(LEVELS):
            next_threshold, next_name = LEVELS[i + 1]
            return current_name, next_threshold, next_name

    return current_name, None, None
