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

class SentenceChunker(Chunker):
    def __init__(
        self,
        stop_symbols: List[str] = ['.', '?', '!'],
        abbreviations: List[str] = ["i.e.", "e.g.", "etc.", "Mr.", "Mrs.", "Dr.", "Prof.", "Inc.", "Ltd."]
    ) -> None:
        self.abbreviations = abbreviations
        self.stop_symbols = stop_symbols

        # Heuristics:
        # - Always merge after titles/latin abbreviations (Mr., Dr., i.e., e.g., etc.)
        # - Conditionally merge after corporate suffixes (Inc., Ltd.) only if the next chunk
        #   starts with lowercase (e.g., "Inc. announced ..."), but allow a true sentence end:
        self.always_merge_after = {
            "Mr.", "Mrs.", "Ms.", "Mx.", "Dr.", "Prof.", "Sr.", "Jr.", "i.e.", "e.g.", "etc."
        }
        self.conditional_merge_after = {"Inc.", "Ltd.", "Co.", "No.", "St.", "Dept."}

        super().__init__()

    def _should_merge(self, left: str, right: str) -> bool:
        """
        Decide if `right` should be merged into `left` (i.e., we split after an abbreviation/initial).
        """
        if not right:
            return False

        # Strip trailing quotes/brackets from the left when checking the last token
        left_clean = left.rstrip().rstrip('"\')]}›»”’)}')

        # Last "word" before the boundary
        m = re.search(r'(\S+)$', left_clean)
        tok = m.group(1) if m else ""

        # cases like "Mr." / "Dr." / "i.e." / "e.g." / "etc."
        if tok in self.always_merge_after:
            return True

        # "Inc." / "Ltd." often continue, but can end a sentence: merge only if next starts lowercase
        if tok in self.conditional_merge_after:
            return bool(re.match(r'^[a-z]', right.strip()))

        # Handle initials like "A." in "A. B. Smith"
        if re.search(r'\b[A-Z]\.$', left_clean):
            return True

        return False

    def chunk(self, text: str) -> List[str]:
        if not text:
            return []

        # Build a safe character class for stop symbols and capture any trailing closing quotes/parens
        stop_chars = re.escape("".join(self.stop_symbols))
        # Match: [.!?]+ possibly followed by closing quotes/brackets, then whitespace,
        # and ensure the next sentence starts with a capital letter.
        pattern = re.compile(rf'([{stop_chars}]+(?:["\')\]]*))\s+(?=[A-Z])')

        parts = re.split(pattern, text)

        # Re-attach the captured punctuation to the left chunk
        stitched: List[str] = []
        i = 0
        while i < len(parts):
            seg = parts[i]
            if i + 1 < len(parts):
                seg = f"{seg}{parts[i + 1]}"
                i += 2
            else:
                i += 1
            if seg.strip():
                stitched.append(seg.strip())

        # Merge false splits caused by abbreviations/initials
        result: List[str] = []
        for seg in stitched:
            if result and self._should_merge(result[-1], seg):
                result[-1] = f"{result[-1]} {seg}"
            else:
                result.append(seg)

        return result


DefaultChunker = SentenceChunker