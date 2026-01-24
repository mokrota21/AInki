from .base import Base
from sqlalchemy import Integer, String, CheckConstraint, DateTime, func, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

class Users(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("permission_level >= 0 AND permission_level <= 10", "chk_permission"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    permission_level: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
