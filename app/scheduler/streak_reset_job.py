import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.database import SessionLocal
from app.models.assignment import DailyAssignment
from app.models.user import AppUser

log = logging.getLogger(__name__)
_IST = ZoneInfo("Asia/Kolkata")


def run_streak_reset_job() -> None:
    log.info("streak_reset_job: starting")
    with SessionLocal() as db:
        user = db.get(AppUser, 1)
        if not user:
            log.warning("streak_reset_job: no seed user found")
            return

        yesterday_ist = (datetime.now(_IST) - timedelta(days=1)).date()

        assignment = db.query(DailyAssignment).filter_by(
            user_id=user.id, assigned_date=yesterday_ist
        ).first()

        if assignment is None:
            log.info("streak_reset_job: no assignment for %s, nothing to do", yesterday_ist)
            return

        if assignment.response is not None:
            log.info(
                "streak_reset_job: assignment for %s already has response=%s, no reset needed",
                yesterday_ist, assignment.response,
            )
            return

        log.info("streak_reset_job: no response for %s — resetting streak", yesterday_ist)
        user.current_streak = 0
        db.commit()
