from pydoc import Doc
from fastapi import FastAPI, UploadFile, HTTPException, status
from pydantic import BaseModel
from src import settings, DefaultReader, FileReader, Chunker, DefaultChunker, Docs, Chunks, DocsMetadata
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid
from fastapi.security import OAuth2PasswordBearer

user = "mokrota"
user_id = "f7ef8cce-efe0-42da-849e-4971a7e5a573"

blob_client = settings.container_client
blob_name = "productiestaten controle rapport 1094 2026-01-14 20-03-45.pdf"

# Download blob as bytes
download_stream = blob_client.download_blob(blob_name)
blob_bytes = download_stream.readall()

print(f"Downloaded {len(blob_bytes)} bytes")
print(type(blob_bytes))  # Should be <class 'bytes'>