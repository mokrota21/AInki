import psycopg2
from dotenv import load_dotenv
from .pg_connection import get_connection
from .neo4j_graph import get_objects, merge_repetition_state
from .repetition import RepeatState
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('ainki.log')  # File output
    ]
)
logger = logging.getLogger(__name__)

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

def assign_objects(user_id: int, chunk_id: int, doc_id: int):
    object_nodes = get_objects(chunk_id, doc_id)
    for object in object_nodes: merge_repetition_state(object.element_id, RepeatState(user_id, 0))
    logger.info(f"Assigned {len(object_nodes)} objects to user {user_id}")
