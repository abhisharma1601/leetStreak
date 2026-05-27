import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.question import Question
from app.models.user import AppUser
from app.services.email_content_builder import build_daily_context
from app.services.email_service import send_daily_email

router = APIRouter(prefix="/admin", tags=["admin"])
log = logging.getLogger(__name__)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/test-email")
def test_email(db: Session = Depends(get_db)):
    user = db.query(AppUser).filter_by(id=1).first()
    if not user:
        raise HTTPException(status_code=404, detail="Seed user not found. Run the app once to seed.")

    question = db.query(Question).first()
    if not question:
        raise HTTPException(status_code=404, detail="No questions seeded yet.")

    from app.models.assignment import DailyAssignment

    # Build a throwaway assignment object (not persisted) just for template context
    fake_assignment = DailyAssignment(
        user_id=user.id,
        question_id=question.id,
        assigned_date=date.today(),
    )

    context = build_daily_context(
        user=user,
        question=question,
        assignment=fake_assignment,
        done_url=f"{settings.app_base_url}/confirm/done?token=TEST_TOKEN",
        skip_url=f"{settings.app_base_url}/confirm/skip?token=TEST_TOKEN",
    )
    try:
        send_daily_email(to=settings.user_email, context=context)
    except Exception as exc:
        log.exception("test-email failed")
        raise HTTPException(status_code=500, detail=f"Email send failed: {exc}")

    return {"status": "sent", "to": settings.user_email, "question": question.title}


@router.post("/trigger-daily-job")
def trigger_daily_job():
    """Manually fire the daily email job — useful for testing without waiting for 21:00 IST."""
    from app.scheduler.daily_email_job import run_daily_email_job
    try:
        run_daily_email_job()
    except Exception as exc:
        log.exception("trigger-daily-job failed")
        raise HTTPException(status_code=500, detail=str(exc))
    return {"status": "job ran"}
