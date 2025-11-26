from .base import Base
from sqlalchemy import Integer, String, CheckConstraint, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class Chunks(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("doc_id", "chunker", "page_no", name='uq_output_constraint')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    md_content: Mapped[str] = mapped_column(String, nullable=False)
    doc_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    chunker: Mapped[str] = mapped_column(String, nullable=False)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
