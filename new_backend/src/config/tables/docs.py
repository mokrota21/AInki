from .base import Base
from sqlalchemy import Integer, String, CheckConstraint, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class Docs(Base):
    __tablename__ = "docs"
    __table_args__ = (
        CheckConstraint("split_no >= 0", name="non-negative_split"),
        UniqueConstraint("filereader", "file_name", name="uq_output_constraint")
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    md_content: Mapped[str] = mapped_column(String, nullable=False)
    split_no: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    filereader: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
