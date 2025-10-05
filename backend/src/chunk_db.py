import os
from dotenv import load_dotenv
import psycopg2
from .pg_connection import get_connection
from typing import List, Dict
from.chunk_maper import map_to_pages

def insert_chunk(chunk: str, page_idx: int, doc_id: int, order_idx: int, reader_name: str) -> int:
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.chunks (content, doc_id, order_idx, page_idx, reader)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (chunk, doc_id, order_idx, page_idx, reader_name)
        )
        id = cursor.fetchone()[0]
        conn.commit()
    return id

def insert_doc_chunks(chunks: List[str], doc_id: int, reader_name: str) -> int:
    conn = get_connection()
    # Deactivating other chunks in the same document
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE public.chunks
            SET "active?" = FALSE
            WHERE doc_id = %s
            """, (doc_id,)
        )
        conn.commit()
    page_mapping = map_to_pages(doc_id, chunks)
    for idx, chunk in enumerate(chunks):
        insert_chunk(chunk, page_mapping[idx], doc_id, idx, reader_name)
    return len(chunks)

def get_chunks(doc_id: int, chunk_ids: List[int] = None) -> List[Dict]:
    conn = get_connection()
    with conn.cursor() as cursor:
        if chunk_ids is None:
            cursor.execute("SELECT id, content, order_idx FROM public.chunks WHERE doc_id = %s ORDER BY order_idx ASC", (doc_id,))
        else:
            cursor.execute("SELECT id, content, order_idx FROM public.chunks WHERE doc_id = %s AND id IN %s ORDER BY order_idx ASC", (doc_id, tuple(chunk_ids)))
        rows = cursor.fetchall()
        return [{"id": row[0], "content": row[1], "order_idx": row[2]} for row in rows]