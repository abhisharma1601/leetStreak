import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import SessionLocal
from app.models.assignment import DailyAssignment
from app.models.user import AppUser
from app.services.email_content_builder import build_daily_context
from app.services.email_service import send_daily_email
from app.services.magic_link_service import generate as generate_token
from app.services.question_picker import pick_next

log = logging.getLogger(__name__)
_IST = ZoneInfo("Asia/Kolkata")


def run_daily_email_job() -> None:
    log.info("daily_email_job: starting")
    with SessionLocal() as db:
        user = db.get(AppUser, 1)
        if not user:
            log.warning("daily_email_job: no seed user found — run the app once to seed")
            return

        today_ist = datetime.now(_IST).date()

        existing = db.query(DailyAssignment).filter_by(
            user_id=user.id, assigned_date=today_ist
        ).first()
        if existing:
            log.info("daily_email_job: already sent for %s, skipping", today_ist)
            return

        question = pick_next(user, db)
        if question is None:
            _send_all_done_email(user)
            return

        assignment = DailyAssignment(
            user_id=user.id,
            question_id=question.id,
            assigned_date=today_ist,
        )
        db.add(assignment)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            log.warning("daily_email_job: race — assignment already inserted for %s", today_ist)
            return

        done_token = generate_token(user.id, assignment.id, "DONE")
        skip_token = generate_token(user.id, assignment.id, "SKIP")

        done_url = f"{settings.app_base_url}/confirm/done?token={done_token}"
        skip_url = f"{settings.app_base_url}/confirm/skip?token={skip_token}"

        context = build_daily_context(
            user=user,
            question=question,
            assignment=assignment,
            done_url=done_url,
            skip_url=skip_url,
        )

        send_daily_email(to=settings.user_email, context=context)

        assignment.sent_at = datetime.now(timezone.utc)
        db.commit()
        log.info("daily_email_job: sent email for question '%s'", question.title)


def _send_all_done_email(user: AppUser) -> None:
    log.info("daily_email_job: user finished all questions — sending celebration email")
    from app.services.email_service import send_email
    html = (
        "<h2>🎉 You finished all 350 LeetCode questions!</h2>"
        f"<p>Total solved: {user.total_solved} | Points: {user.total_points} | "
        f"Longest streak: {user.longest_streak} days</p>"
        "<p>Review mode coming soon. Take a break, you've earned it.</p>"
    )
    send_email(
        to=user.email,
        subject="LeetStreak — You finished all 350! 🎉",
        html_body=html,
    )
