from .base import Base
from sqlalchemy import Integer, String, CheckConstraint, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class Users(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("permission_level >= 0 AND permission_level <= 10", "chk_permission"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    permission_level: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
