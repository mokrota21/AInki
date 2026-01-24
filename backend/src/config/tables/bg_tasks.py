from .base import Base, after_create
from sqlalchemy import Integer, String, CheckConstraint, DateTime, func, UniqueConstraint, event, UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class TaskStatus(Base):
    __tablename__ = "task_status"
    __table_args__ = (
        UniqueConstraint("task_id", name="uq_task_status_task_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
