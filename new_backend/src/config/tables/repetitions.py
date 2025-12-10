from datetime import datetime
from .base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, func

class Repetitions(Base):
    __tablename__ = "repetitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    last_repeated: Mapped[datetime] = mapped_column(DateTime)
    knowledge_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
