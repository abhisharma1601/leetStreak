from datetime import datetime, timezone

from app.models.assignment import DailyAssignment
from app.models.question import Question
from app.models.user import AppUser

_BASE_POINTS = {"EASY": 1, "MEDIUM": 3, "HARD": 6}


def _multiplier(new_streak: int) -> float:
    if new_streak >= 100:
        return 2.0
    if new_streak >= 30:
        return 1.5
    if new_streak >= 7:
        return 1.2
    return 1.0


def apply_done(user: AppUser, question: Question, assignment: DailyAssignment) -> int:
    """Apply a DONE response. Returns points earned."""
    user.total_solved += 1
    new_streak = user.current_streak + 1
    base = _BASE_POINTS[question.difficulty]
    earned = round(base * _multiplier(new_streak))
    user.total_points += earned
    user.current_streak = new_streak
    user.longest_streak = max(user.longest_streak, user.current_streak)
    user.next_question_index += 1
    assignment.response = "DONE"
    assignment.responded_at = datetime.now(timezone.utc)
    return earned


def apply_skip(user: AppUser, assignment: DailyAssignment) -> None:
    user.current_streak = 0
    assignment.response = "SKIP"
    assignment.responded_at = datetime.now(timezone.utc)
