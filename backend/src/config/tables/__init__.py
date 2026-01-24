# Import all table models to ensure they register with Base.metadata
from .users import Users
from .repetitions import Repetitions
from .docs import Docs
from .chunks import Chunks
from .base import Base, after_create
from .docs_metadata import DocsMetadata
from .knowledge import Knowledge
from .bg_tasks import TaskStatus
__all__ = ["Users", "Repetitions", "Docs", "Chunks", "Base", "DocsMetadata", "Knowledge", "TaskStatus", "after_create"]

