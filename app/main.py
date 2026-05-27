import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import user, question, assignment, consumed_token  # noqa: F401 — register with Base


logging.basicConfig(level=settings.log_level.upper())


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.seed.seed_questions import seed_db
    from app.scheduler.scheduler import start, stop
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_db(db)
    start()
    yield
    stop()


app = FastAPI(title="LeetStreak", lifespan=lifespan)

from app.routes import admin, confirm, respond  # noqa: E402
app.include_router(admin.router)
app.include_router(confirm.router)
app.include_router(respond.router)


@app.get("/health")
def health():
    return {"status": "ok"}
