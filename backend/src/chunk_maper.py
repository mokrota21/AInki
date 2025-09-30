from .pg_connection import get_connection

def chunk_maper(doc_id: int, chunk_id_s: int, chunk_id_e: int) -> str:
    conn = get_connection()
    content = ""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT content FROM public.chunks WHERE doc_id = %s AND order_idx BETWEEN %s AND %s
            """,
            (doc_id, chunk_id_s, chunk_id_e)
        )
        for row in cursor.fetchall():
            content += row[0]
    return content