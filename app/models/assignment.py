from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DailyAssignment(Base):
    __tablename__ = "daily_assignment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("app_user.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("question.id"), nullable=False)
    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # NULL | DONE | SKIP
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "assigned_date", name="uq_assignment_user_date"),
        Index("idx_assignment_user_date", "user_id", "assigned_date"),
        Index("idx_assignment_user_response", "user_id", "response"),
    )
