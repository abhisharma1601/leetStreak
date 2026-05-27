import hashlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import jwt

from app.config import settings

_IST = ZoneInfo("Asia/Kolkata")


def _expiry_epoch() -> int:
    now_ist = datetime.now(_IST)
    tomorrow = (now_ist + timedelta(days=1)).date()
    expiry = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 9, 0, 0, tzinfo=_IST)
    return int(expiry.timestamp())


def generate(user_id: int, assignment_id: int, action: str) -> str:
    payload = {
        "sub": user_id,
        "aid": assignment_id,
        "act": action,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": _expiry_epoch(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def mark_consumed(token: str, db) -> None:
    from app.models.consumed_token import ConsumedToken
    db.add(ConsumedToken(token_hash=token_hash(token)))
    db.commit()


def is_consumed(token: str, db) -> bool:
    from app.models.consumed_token import ConsumedToken
    return db.get(ConsumedToken, token_hash(token)) is not None
