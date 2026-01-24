from abc import ABC, abstractmethod
from typing import List, Dict, Any
import re
from .config.settings import settings

class Chunker(ABC):
    def __init__(self) -> None:
        self.name="UndefinedChunker"

    @abstractmethod
    def chunk(self, pages_text: List[str]) -> List[Dict[str, Any]]:
        """
        Chunks pages texts. Returns list of chunks.
        """
        pass

class SimpleChunker(Chunker):
    def __init__(self, chunk_size: int = settings.chunk_size, stride: int = settings.stride) -> None:
        super().__init__()
        self.chunk_size = chunk_size
        self.stride = stride
        self.name="SimpleChunker"

    def chunk(self, pages_text: List[str]) -> List[Dict[str, Any]]:
        chunks = []
        buffer = ""
        for page_num, page_text in enumerate(pages_text):
            buffer += page_text
            while len(buffer) >= self.chunk_size:
                chunks.append(
                    {
                        "text": buffer[:self.chunk_size],
                        "page_no": page_num
                    }
                )
                buffer = buffer[self.stride:]
                
        if buffer:
            chunks.append(
                {
                    "text": buffer,
                    "page_no": page_num,
                }
            )
        return chunks

DefaultChunker = SimpleChunker
