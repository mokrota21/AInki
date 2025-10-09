from abc import ABC, abstractmethod
from typing import List
import re

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


import re
from typing import List

class SentenceChunker:
    def __init__(self) -> None:
        self.abbreviations = {
            'e.g.', 'i.e.', 'etc.', 'vs.', 'cf.', 'viz.', 'ex.', 'inc.',
            'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Sr.', 'Jr.', 'St.',
            'Ltd.', 'Co.', 'Corp.', 'Inc.', 'LLC', 'U.S.', 'U.K.',
            'D.C.', 'E.U.', 'A.I.'
        }
        self.abbrev_pattern = re.compile(
            r'(?:' + '|'.join(map(re.escape, self.abbreviations)) + r')\s*$'
        )
        self.sentence_end_re = re.compile(
            r'[.!?]+(?:[\'")\]]+)?(?=(?:\s*\n*\s*[A-Z]|$))'
        )

    def chunk(self, text: str) -> List[str]:
        if not text:
            return []

        sentences = []
        start = 0

        for match in self.sentence_end_re.finditer(text):
            end = match.end()
            candidate = text[start:end]

            # check if this punctuation is part of an abbreviation
            if self._ends_with_abbreviation(candidate):
                continue  # don't split yet
            else:
                # include everything up to end of punctuation
                sentences.append(text[start:end])
                start = end

        # append the rest
        if start < len(text):
            sentences.append(text[start:])

        return sentences

    def _ends_with_abbreviation(self, text: str) -> bool:
        if self.abbrev_pattern.search(text):
            return True
        if re.search(r'\b[A-Z]\.\s*$', text):
            return True
        if re.search(r'\b(?:[A-Z]\.){2,}\s*$', text):
            return True
        return False

# TODO: figure out how to automatically keep one topic in one chunk.
class LowerBoundChunker(SentenceChunker):
    def __init__(self, lower_bound: int = 1000) -> None:
        self.lower_bound = lower_bound
        super().__init__()
    
    def chunk(self, text: str) -> List[str]:
        chunks = super().chunk(text)
        new_chunks = []
        current_chunk = ""
        for chunk in chunks:
            if len(current_chunk) >= self.lower_bound:
                new_chunks.append(current_chunk)
                current_chunk = ""
            current_chunk += chunk
        if current_chunk:
            new_chunks.append(current_chunk)
        return new_chunks

DefaultChunker = LowerBoundChunker
