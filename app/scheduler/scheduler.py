import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.scheduler.daily_email_job import run_daily_email_job
from app.scheduler.streak_reset_job import run_streak_reset_job

log = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

scheduler.add_job(
    run_daily_email_job,
    trigger="cron",
    hour=21,
    minute=30,
    id="daily_email",
    replace_existing=True,
)

scheduler.add_job(
    run_streak_reset_job,
    trigger="cron",
    hour=0,
    minute=0,
    id="streak_reset",
    replace_existing=True,
)


def start() -> None:
    scheduler.start()
    log.info("Scheduler started — daily email at 21:00 IST, streak reset at 00:00 IST")


def stop() -> None:
    scheduler.shutdown(wait=False)
    log.info("Scheduler stopped")
