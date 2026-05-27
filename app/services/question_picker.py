from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.question import Question
from app.models.user import AppUser


def pick_next(user: AppUser, db: Session) -> Question | None:
    questions = db.execute(
        select(Question).order_by(Question.id)
    ).scalars().all()

    if user.next_question_index >= len(questions):
        return None

    return questions[user.next_question_index]
