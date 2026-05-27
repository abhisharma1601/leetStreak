from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    leetcode_slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(Text, nullable=False)  # EASY | MEDIUM | HARD
    url: Mapped[str] = mapped_column(Text, nullable=False)
    topics: Mapped[str] = mapped_column(Text, nullable=False)  # comma-separated
