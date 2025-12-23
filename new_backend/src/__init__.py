from .filereader import FileReader, DefaultReader
from .chunker import Chunker, DefaultChunker
from .config.tables import *  # noqa: F403, F401
from .config import tables as _tables
from .config.settings import settings

# Base exports
_base_exports = [
    "settings",
    "FileReader",
    "DefaultReader",
    "Chunker",
    "DefaultChunker",
]

# Dynamically include all exports from tables module
_table_exports = getattr(_tables, "__all__", [])

__all__ = _base_exports + _table_exports