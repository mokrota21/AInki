from abc import ABC, abstractmethod
from typing import List

class Chunker(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        """Chunks given text. Returns list of chunks
        text: str - piece of text to chunk."""
        pass

class SimpleChunker(Chunker):
    def __init__(self, chunk_size: int, stride: int) -> None:
        self.chunk_size = chunk_size
        self.stride = stride
        super().__init__()

    def chunk(self, text: str) -> List[str]:
        chunks = []
        for i in range(0, len(text), self.stride):
            chunks.append(text[i:i+self.chunk_size])
        return chunks

DefaultChunker = SimpleChunker