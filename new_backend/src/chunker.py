from abc import ABC, abstractmethod
from typing import List, Dict, Any
import re

class Chunker(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def chunk(self, pages_text: List[str]) -> List[Dict[str, Any]]:
        """
        Chunks pages texts. Returns list of chunks.
        """
        pass

class SimpleChunker(Chunker):
    def __init__(self, chunk_size: int, stride: int) -> None:
        self.chunk_size = chunk_size
        self.stride = stride
        super().__init__()

    def chunk(self, pages_text: List[str]) -> List[Dict[str, Any]]:
        chunks = []
        chunk = ""
        for page_num, page_text in enumerate(pages_text):
            for i in range(0, len(page_text), self.stride):
                chunk += page_text[i:i+self.chunk_size]
                if len(chunk) >= self.chunk_size:
                    chunks.append(
                        {
                            "text": chunk,
                            "page_num": page_num,
                        }
                    )
                    chunk = chunk[self.stride:]
        if chunk:
            chunks.append(
                {
                    "text": chunk,
                    "page_num": page_num,
                }
            )
        return chunks

DefaultChunker = SimpleChunker
