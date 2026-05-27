from app.models.assignment import DailyAssignment
from app.models.question import Question
from app.models.user import AppUser
from app.services.guilt_message_service import pick as pick_guilt
from app.services.level_service import level_for_points


def build_daily_context(
    user: AppUser,
    question: Question,
    assignment: DailyAssignment,
    done_url: str,
    skip_url: str,
    total_questions: int = 350,
) -> dict:
    level_name, next_threshold, next_level_name = level_for_points(user.total_points)

    if next_threshold is not None:
        points_needed = next_threshold - user.total_points
    else:
        points_needed = 0

    from app.config import settings as _settings

    return {
        "user": user,
        "display_name": _settings.user_display_name,
        "question": question,
        "assignment": assignment,
        "done_url": done_url,
        "skip_url": skip_url,
        "guilt_text": pick_guilt(user.current_streak),
        "level_name": level_name,
        "next_level_name": next_level_name,
        "next_threshold": next_threshold,
        "points_needed": points_needed,
        "total_questions": total_questions,
        "difficulty_color": {
            "EASY": "#00b894",
            "MEDIUM": "#e17055",
            "HARD": "#d63031",
        }.get(question.difficulty, "#636e72"),
        "difficulty_label": question.difficulty.capitalize(),
        "topics_list": [t.strip() for t in question.topics.split(",")],
    }
