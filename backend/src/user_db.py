import psycopg2
from dotenv import load_dotenv
from .pg_connection import get_connection

def insert_user(gmail: str, password: str, username: str):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.users (gmail, password, name)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (gmail, password, username)
        )
        id = cursor.fetchone()[0]
        conn.commit()
    return id

def authorize_user(password: str, name_or_gmail: str):
    assert name_or_gmail is not None
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id FROM public.users WHERE password = %s AND (name = %s OR gmail = %s)
            """,
            (password, name_or_gmail, name_or_gmail)
        )
        result = cursor.fetchone()
        if result:
            id = result[0]
        else:
            id = None
    return id