import logging

import jwt
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.models.assignment import DailyAssignment
from app.models.question import Question
from app.models.user import AppUser
from app.services import magic_link_service
from app.services.level_service import level_for_points
from app.services.streak_service import apply_done, apply_skip

router = APIRouter()
templates = Jinja2Templates(directory="app/templates/web")
log = logging.getLogger(__name__)


@router.post("/respond")
def respond(
    request: Request,
    token: str = Form(...),
    action: str = Form(...),
    db=Depends(get_db),
):
    # 1. Verify JWT
    try:
        payload = magic_link_service.verify(token)
    except jwt.ExpiredSignatureError:
        return templates.TemplateResponse("responded.html", {
            "request": request,
            "error": "This link has expired.",
        })
    except Exception:
        return templates.TemplateResponse("responded.html", {
            "request": request,
            "error": "Invalid or malformed link.",
        })

    # action in body must match JWT claim
    if payload.get("act") != action:
        return templates.TemplateResponse("responded.html", {
            "request": request,
            "error": "Action mismatch — please use the original email links.",
        })

    # 2. Replay check
    if magic_link_service.is_consumed(token, db):
        return templates.TemplateResponse("already_done.html", {"request": request})

    # 3. Load assignment
    assignment = db.get(DailyAssignment, payload["aid"])
    if not assignment or assignment.responded_at is not None:
        return templates.TemplateResponse("already_done.html", {"request": request})

    user = db.get(AppUser, assignment.user_id)
    question = db.get(Question, assignment.question_id)

    old_level_name = level_for_points(user.total_points)[0]

    # 4. Mutate in a transaction
    earned = 0
    if action == "DONE":
        earned = apply_done(user, question, assignment)
    else:
        apply_skip(user, assignment)

    from app.models.consumed_token import ConsumedToken
    db.add(ConsumedToken(token_hash=magic_link_service.token_hash(token)))
    db.add(user)
    db.add(assignment)
    db.commit()

    new_level_name = level_for_points(user.total_points)[0]

    return templates.TemplateResponse("responded.html", {
        "request": request,
        "action": action,
        "current_streak": user.current_streak,
        "longest_streak": user.longest_streak,
        "total_solved": user.total_solved,
        "total_points": user.total_points,
        "earned_points": earned,
        "level_name": new_level_name,
        "level_up": new_level_name != old_level_name,
        "old_level_name": old_level_name,
        "question_title": question.title,
    })
