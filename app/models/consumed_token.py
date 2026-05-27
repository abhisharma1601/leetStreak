from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConsumedToken(Base):
    __tablename__ = "consumed_token"

    token_hash: Mapped[str] = mapped_column(Text, primary_key=True)  # SHA256 hex of the JWT
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
