# Import all table models to ensure they register with Base.metadata
from .users import Users
from .repetitions import Repetitions
from .docs import Docs
from .chunks import Chunks
from .base import Base, after_create

__all__ = ["Users", "Repetitions", "Docs", "Chunks", "Base", "after_create"]

