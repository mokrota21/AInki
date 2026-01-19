from .base import Base
from sqlalchemy import String, DateTime, func, UUID, Text
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class Knowledge(Base):
    __tablename__ = "knowledge"

    knowledge_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    doc_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)  # References docs_metadata.doc_id
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)  # References chunks.id
    knowledge_name: Mapped[str] = mapped_column(String, nullable=False)  # Name of the topic/knowledge object
    knowledge_question: Mapped[str] = mapped_column(Text, nullable=False)  # Question to test understanding
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(), server_default=func.now())
