from abc import ABC, abstractmethod
from typing import Any
from fastapi import UploadFile
from io import BytesIO

class FileReader(ABC):
    def __init__(self) -> None:
        pass
        self.name = "UndefinedReader"
    
    @abstractmethod
    def read_file(self, file: UploadFile) -> Any:
        pass

from PyPDF2 import PdfReader

class PDFReader(FileReader):
    def __init__(self) -> None:
        super().__init__()
        self.name = "PDFReader"
    
    def read_file(self, file: UploadFile) -> Any:
        bytes = file.file.read()
        pages = PdfReader(BytesIO(bytes)).pages
        contents = " ".join([page.extract_text() for page in pages])
        return (contents, None)

import subprocess
import os

class MineruReader(FileReader):
    def __init__(self) -> None:
        super().__init__()
        self.name = "MineruReader"
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
        upload_path = os.path.join(path, "uploads")
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        output_path = os.path.join(path, "output")
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        self.upload_path = upload_path
        self.output_path = output_path

    def read_file(self, file: UploadFile) -> Any:
        file_path = os.path.join(self.upload_path, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        subprocess.run(["mineru", "-p", file_path, "-o", self.output_path, "-m", "auto", "-l", "en", "-d", "cuda", "--vram", "5"])
        result_folder = os.path.join(self.output_path, os.path.basename(file_path).split(".")[0], "auto")
        with open(os.path.join(result_folder, os.path.basename(file_path).replace(".pdf", ".md")), "r", encoding="utf-8") as f:
            contents = f.read()
        return (contents, result_folder)

DefaultReader = MineruReader