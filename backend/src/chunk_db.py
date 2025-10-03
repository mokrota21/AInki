import os
from dotenv import load_dotenv
import psycopg2
from .pg_connection import get_connection
from typing import List, Dict

def insert_chunk(chunk: str, doc_id: int, order_idx: int, reader_name: str) -> int:
    conn = get_connection()
    char_count = len(chunk)
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.chunks (content, doc_id, order_idx, char_count, reader)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (chunk, doc_id, order_idx, char_count, reader_name)
        )
        id = cursor.fetchone()[0]
        conn.commit()
    return id

def get_chunks(doc_id: int, chunk_ids: List[int] = None) -> List[Dict]:
    conn = get_connection()
    with conn.cursor() as cursor:
        if chunk_ids is None:
            cursor.execute("SELECT id, content, order_idx FROM public.chunks WHERE doc_id = %s ORDER BY order_idx ASC", (doc_id,))
        else:
            cursor.execute("SELECT id, content, order_idx FROM public.chunks WHERE doc_id = %s AND id IN %s ORDER BY order_idx ASC", (doc_id, tuple(chunk_ids)))
        rows = cursor.fetchall()
        return [{"id": row[0], "content": row[1], "order_idx": row[2]} for row in rows]