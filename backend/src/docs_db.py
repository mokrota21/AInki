import psycopg2
from fastapi import UploadFile
from io import BytesIO
import logging
from .pg_connection import get_connection
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # This makes it show in terminal
    ]
)

logger = logging.getLogger(__name__)

def insert_doc(doc: UploadFile, folder: str = None, force: bool = False) -> int:
    """
    For insterting data in doc table
    conn: connection to db;
    doc: fastapi uploadfile object.
    """
    conn = get_connection()
    name = doc.filename
    size = doc.size / 1048576

    # Check if doc already exists
    with conn.cursor() as cursor:
        if not force:
            cursor.execute(
                """
                SELECT * FROM public.docs_metadata WHERE name = %s
                """,
                (name)
            )
            result = cursor.fetchone()
            if result:
                logger.info(f"Doc {name} already exists")
                return -1
        else:
            cursor.execute(
                """
                DELETE FROM public.docs_metadata WHERE name = %s
                """,
                (name,)
            )
            if cursor.rowcount > 0:
                logger.info(f"Doc {name} deleted")
            else:
                logger.info(f"No document with name {name} found")

    # Otherwise insert
    with conn.cursor() as cursor: # TODO: fix pathing
        insert_sql = """
        INSERT INTO public.docs_metadata (name, size_mb, folder)
        VALUES (%s, %s, %s)
        RETURNING id;
        """
        cursor.execute(insert_sql, (name, size, folder))
        id = cursor.fetchone()[0]
        conn.commit()

    return id

def get_all_docs() -> List[Dict]:
    """
    Return a list of document metadata with stable field names.
    Only returns the minimal fields needed by the frontend to avoid relying on
    implicit column order from SELECT *.
    """
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name FROM public.docs_metadata ORDER BY id")
        rows = cursor.fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]

def get_doc(doc_id: int) -> Dict:
    """
    Return a document metadata with stable field names.
    """
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, folder FROM public.docs_metadata WHERE id = %s", (doc_id,))
        row = cursor.fetchone()
        return {"id": row[0], "name": row[1], "folder": row[2]}