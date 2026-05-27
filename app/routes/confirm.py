import logging

import jwt
from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.models.assignment import DailyAssignment
from app.models.question import Question
from app.models.user import AppUser
from app.services import magic_link_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates/web")
log = logging.getLogger(__name__)


def _render_confirm(request: Request, token: str, expected_action: str, db):
    # 1. Verify JWT
    try:
        payload = magic_link_service.verify(token)
    except jwt.ExpiredSignatureError:
        return templates.TemplateResponse("responded.html", {
            "request": request,
            "error": "This link has expired. Tokens are valid until 9 AM the next day.",
        })
    except Exception:
        return templates.TemplateResponse("responded.html", {
            "request": request,
            "error": "Invalid or malformed link.",
        })

    if payload.get("act") != expected_action:
        return templates.TemplateResponse("responded.html", {
            "request": request,
            "error": "Invalid link.",
        })

    # 2. Replay check
    if magic_link_service.is_consumed(token, db):
        return templates.TemplateResponse("already_done.html", {"request": request})

    # 3. Load assignment
    assignment = db.get(DailyAssignment, payload["aid"])
    if not assignment or assignment.responded_at is not None:
        return templates.TemplateResponse("already_done.html", {"request": request})

    question = db.get(Question, assignment.question_id)
    user = db.get(AppUser, assignment.user_id)

    return templates.TemplateResponse("confirm.html", {
        "request": request,
        "action": expected_action,
        "token": token,
        "question": question,
        "current_streak": user.current_streak,
    })


@router.get("/confirm/done")
def confirm_done(request: Request, token: str = Query(...), db=Depends(get_db)):
    return _render_confirm(request, token, "DONE", db)


@router.get("/confirm/skip")
def confirm_skip(request: Request, token: str = Query(...), db=Depends(get_db)):
    return _render_confirm(request, token, "SKIP", db)
