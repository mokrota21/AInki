import os
from dotenv import load_dotenv
import psycopg2
from .pg_connection import get_connection

def insert_chunk(chunk: str, doc_id: int, order_idx: int) -> int:
    conn = get_connection()
    char_count = len(chunk)
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.chunks (content, doc_id, order_idx, char_count)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (chunk, doc_id, order_idx, char_count)
        )
        id = cursor.fetchone()[0]
        conn.commit()
    return id