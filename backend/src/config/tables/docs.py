from .base import Base
from sqlalchemy import Integer, String, CheckConstraint, DateTime, func, UniqueConstraint, UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class Docs(Base):
    __tablename__ = "docs"
    __table_args__ = (
        CheckConstraint("page_no >= 0", name="non_negative_page"),
        UniqueConstraint("filereader", "file_name", "user_id", "page_no", name="uq_docs_filereader")
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    doc_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)  # Set manually - same for all pages of one document
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    md_content: Mapped[str] = mapped_column(String, nullable=False)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    filereader: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    # TODO: add document_mapping table that caches processed tables across users