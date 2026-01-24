from .base import Base, after_create
from sqlalchemy import Integer, String, CheckConstraint, DateTime, func, UniqueConstraint, event, UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class Chunks(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("doc_id", "chunker", "page_no", "chunk_no", name='uq_output_constraint_chunker'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    md_content: Mapped[str] = mapped_column(String, nullable=False)
    chunk_no: Mapped[int] = mapped_column(Integer, nullable=False)
    doc_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    chunker: Mapped[str] = mapped_column(String, nullable=False)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
