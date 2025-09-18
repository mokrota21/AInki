from abc import ABC, abstractmethod
from typing import Any
from io import BytesIO

class FileReader(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def read_file(self, file: BytesIO) -> Any:
        pass

from PyPDF2 import PdfReader

class PDFReader(FileReader):
    def __init__(self) -> None:
        super().__init__()
    
    def read_file(self, file: BytesIO) -> Any:
        pages = PdfReader(file).pages
        contents = " ".join([page.extract_text() for page in pages])
        return contents

DefaultReader = PDFReader