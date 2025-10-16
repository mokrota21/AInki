from abc import ABC, abstractmethod
from typing import Any
from fastapi import UploadFile
from io import BytesIO
import os
import logging
from .paths import output_path, upload_path, get_output_folder
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("DOC_ENDPOINT")
key = os.getenv("DOC_KEY")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('ainki.log')  # File output
    ]
)
logger = logging.getLogger(__name__)

class FileReader(ABC):
    def __init__(self) -> None:
        pass
        self.name = "UndefinedReader"
    
    @abstractmethod
    def read_file(self, file: UploadFile) -> Any:
        pass

# from PyPDF2 import PdfReader

# class PDFReader(FileReader):
#     def __init__(self) -> None:
#         super().__init__()
#         self.name = "PDFReader"
    
#     def read_file(self, file: UploadFile) -> Any:
#         bytes = file.file.read()
#         pages = PdfReader(BytesIO(bytes)).pages
#         contents = " ".join([page.extract_text() for page in pages])
#         return (contents, None)

import subprocess
import os

class MineruReader(FileReader):
    def __init__(self) -> None:
        super().__init__()
        self.name = "MineruReader"

    def read_file(self, file: UploadFile) -> Any:
        file_path = os.path.join(upload_path, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        backend = "pipeline"
        final_path = os.path.join(output_path, file.filename)
        if not os.path.exists(final_path):
            subprocess.run(["mineru", "-p", file_path, "-o", output_path, "-m", "auto", "-l", "en", "-d", "cuda", "--vram", "5", "-b", backend]) #, "-b", "vlm-transformers")
        else:
            logger.info(f"Found existing processed file in path: {output_path}")
        result_folder = get_output_folder(file_path)
        with open(os.path.join(result_folder, os.path.basename(file_path).replace(".pdf", ".md")), "r", encoding="utf-8") as f:
            contents = f.read()
        return (contents, result_folder)

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

class DocIntelligenceReader(FileReader):
    def __init__(self) -> None:
        super().__init__()
        self.name = "DocIntelligence"
        self.client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))

    def read_file(self, file: UploadFile) -> Any:
        bin_content = file.file.read()
        poller = self.client.begin_analyze_document("prebuilt-layout", bin_content, output_content_format="markdown")
        result = poller.result()
        return (result.content, None)

DefaultReader = DocIntelligenceReader