import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.question import Question
from app.models.user import AppUser

logger = logging.getLogger(__name__)

_SEED_FILE = Path(__file__).parent.parent.parent / "seed_data" / "leetcode_350.json"


def seed_db(db: Session) -> None:
    _seed_questions(db)
    _seed_user(db)


def _seed_questions(db: Session) -> None:
    if db.query(Question).count() > 0:
        return

    data = json.loads(_SEED_FILE.read_text(encoding="utf-8"))
    db.add_all([Question(**q) for q in data])
    db.commit()
    logger.info("Seeded %d questions", len(data))


def _seed_user(db: Session) -> None:
    if db.query(AppUser).count() > 0:
        return

    user = AppUser(email=settings.user_email)
    db.add(user)
    db.commit()
    logger.info("Seeded user: %s", settings.user_email)
