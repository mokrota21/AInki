from abc import ABC, abstractmethod
from typing import Any, List
from io import BytesIO
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('ainki.log')  # File output
    ]
)
logger = logging.getLogger(__name__)
from .config.settings import settings

class FileReader(ABC):
    def __init__(self) -> None:
        pass
        self.name = "UndefinedReader"
        self.supported_file_types = None

    def get_name(self) -> str:
        return self.name

    @abstractmethod
    def get_md(self, file_bytes: bytes, file_type: str) -> List[str]:
        pass

class DocIntelligenceReader(FileReader):
    def __init__(self) -> None:
        super().__init__()
        self.name = "DocIntelligence"

    def get_md(self, file_bytes: bytes, file_type: str) -> Any:
        if self.supported_file_types is not None and file_type not in self.supported_file_types:
            raise ValueError(f"File type {file_type} is not supported")
        poller = settings.doc_client.begin_analyze_document(settings.doc_model_id, file_bytes, output_content_format="markdown")
        result = poller.result()
        content = result.content
        pages = content.split("<!-- PageBreak -->")
        return pages

DefaultReader = DocIntelligenceReader
