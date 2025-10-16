import os
from io import BytesIO, BufferedReader
from typing import Optional, Union

from azure.storage.blob import BlobServiceClient


_blob_service_client: Optional[BlobServiceClient] = None


def _get_blob_service_client() -> BlobServiceClient:
    global _blob_service_client
    if _blob_service_client is not None:
        return _blob_service_client

    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

    if connection_string:
        _blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        return _blob_service_client

    if not account_name or not account_key:
        raise RuntimeError(
            "Azure Storage credentials are not configured. Set AZURE_STORAGE_CONNECTION_STRING or both AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY."
        )

    account_url = f"https://{account_name}.blob.core.windows.net"
    _blob_service_client = BlobServiceClient(account_url=account_url, credential=account_key)
    return _blob_service_client


def _get_primary_container_name() -> str:
    names = os.getenv("AZURE_STORAGE_CONTAINER_NAMES", "").split(",")
    names = [n.strip() for n in names if n.strip()]
    if not names:
        raise RuntimeError("AZURE_STORAGE_CONTAINER_NAMES is not set or empty")
    return names[0]


def store_file(doc_id: int, file_obj: Union[BytesIO, bytes, BufferedReader, "UploadFile"]) -> str:
    """Upload a PDF to Azure Blob Storage as "{doc_id}.pdf" into the primary container.

    Returns the blob URL.
    """
    container = _get_primary_container_name()
    blob_name = f"{doc_id}.pdf"
    bsc = _get_blob_service_client()
    blob_client = bsc.get_blob_client(container=container, blob=blob_name)

    # Ensure container exists (no-op if it already exists)
    try:
        bsc.create_container(container)
    except Exception:
        # Likely already exists or insufficient perms to create; ignore
        pass

    # Normalize input to bytes-like stream
    data: Union[BytesIO, bytes]
    try:
        # FastAPI UploadFile compatibility without import cycle
        from starlette.datastructures import UploadFile  # type: ignore
        if isinstance(file_obj, UploadFile):  # type: ignore
            file_obj.file.seek(0)
            data = file_obj.file.read()
        else:
            raise ImportError  # jump to except path
    except Exception:
        if isinstance(file_obj, (bytes, bytearray)):
            data = bytes(file_obj)
        elif hasattr(file_obj, "read"):
            # File-like object
            try:
                file_obj.seek(0)  # type: ignore
            except Exception:
                pass
            data = file_obj.read()
        else:
            raise TypeError("Unsupported file_obj type for store_file")

    blob_client.upload_blob(data, overwrite=True, content_type="application/pdf")
    return blob_client.url


def fet_file(doc_id: int) -> bytes:
    """Download the PDF bytes for the given doc_id from Azure Blob Storage."""
    container = _get_primary_container_name()
    blob_name = f"{doc_id}.pdf"
    bsc = _get_blob_service_client()
    blob_client = bsc.get_blob_client(container=container, blob=blob_name)
    stream = blob_client.download_blob()
    return stream.readall()


