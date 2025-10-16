from neo4j import GraphDatabase
from neo4j.graph import Node
from dotenv import load_dotenv
import os
from .repetition import RepeatState
from datetime import timezone, datetime
from .neo4j_connection import driver
from random import choice
from .chunk_db import get_max_chunk_order

tz = timezone.utc


def add_relation(node1_id: str, node2_id: str):
    """
    Connects two nodes as related. Relation is symmetric property
    """

    summary = driver.execute_query(
        """
        MATCH (a), (b)
        WHERE a.id = $id1, b.id = $id2
        CREATE (a)-[r:Related_to]-(b)
        RETURN r
        """,
        id1 = node1_id, id2 = node2_id
    )
    return summary.records[0]["r"]

def add_knowledge_object(name: str, label: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add a knowledge object to the NEO4j graph with the specified label.
    
    Args:
        name: Name of the object
        label: Neo4j label for the object (e.g., 'Definition', 'Theorem', 'Fact', etc.)
        doc_id: ID of document it is taken from
        chunk_id_s: Starting chunk ID where object begins
        chunk_id_e: Ending chunk ID where object ends
    
    Returns:
        The created node
    """
    assert chunk_id_e >= chunk_id_s
    assert label is not None and label.strip() != ""

    # Use parameterized query to prevent injection
    query = f"CREATE (n:BookKnowledge {{type: $type, name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}}) RETURN n"
    
    summary = driver.execute_query(
        query,
        type=label, name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["n"]

def add_review_question(node_id: str, question: str, question_type: str, cognitive_focus: str, answer: str):
    """
    Create a ReviewQuestion and link it to an existing BookKnowledge node.
    Fails cleanly if the BookKnowledge node doesn't exist.
    """
    query = """
    MATCH (m)
    WHERE elementId(m) = $node_id
    CREATE (n:ReviewQuestion {type: $type, question: $question, answer: $answer, cognitive_focus: $cognitive_focus, asked: $asked, correct: $correct, asked_at: $asked_at})
    CREATE (n)-[:QUESTION_FOR]->(m)
    RETURN n
    """
    result = driver.execute_query(
        query,
        node_id=node_id,
        type=question_type,
        question=question,
        answer=answer,
        cognitive_focus=cognitive_focus,
        asked=0,
        correct=0,
        asked_at=datetime.now(tz)
    )
    records = result.records
    if not records:
        raise ValueError(f"No BookKnowledge node found with id={node_id!r}")
    return records[0]["n"]


def init_graph():
    # Make constraint on userid
    try:
        driver.execute_query(
            "CREATE CONSTRAINT userid_constraint FOR (n:User) REQUIRE n.userid IS UNIQUE"
        )
    except:
        pass
    

# TODO: test this
def merge_repetition_state(connected_to_id: str, state: RepeatState):
    state_val = state.state
    userid = state.userid
    next_repeat = state.get_next_repeat()
    result = driver.execute_query(
        """
        MATCH (n)
        WHERE elementId(n) = $n_id
        MERGE (n)-[c:LAST_REPEATED]->(r:RepetitionState {userid: $userid})
        ON CREATE SET r.last_repeated = datetime({year: 1, month: 1, day: 1, hour: 0, minute: 0, second: 0, millisecond: 0, microsecond: 0, nanosecond: 0, timezone: 'UTC'})
        ON MATCH SET r.last_repeated = datetime()
        SET r.next_repeat = $next_repeat
        SET r.state = $state
        RETURN r, c
        """,
        n_id=connected_to_id, next_repeat=next_repeat, userid=userid, state=state_val
    )
    driver.execute_query(
        """
        MATCH (R)
        WHERE elementId(R) = $r_id
        MERGE (U:User {userid: $userid})
        MERGE (R)-[:of]->(U)
        """,
        r_id=result.records[0]["r"].element_id, userid=userid
    )
    return result.records[0]["r"], result.records[0]["c"]

def get_all_assigned(userid: str = None):
    result = driver.execute_query(
        """
        MATCH (n)-[c:LAST_REPEATED]->(r:RepetitionState)
        WHERE r.userid = $userid OR $userid IS NULL
        RETURN n, c, r
        """,
        userid=userid
    )
    return result.records

def get_all_pending(userid: str = None):
    result = driver.execute_query(
        """
        MATCH (n)-[c:LAST_REPEATED]->(r:RepetitionState)
        WHERE r.next_repeat < datetime() AND (r.userid = $userid OR $userid IS NULL)
        RETURN n, c, r
        """,
        userid=userid
    )
    return result.records

def get_objects(chunk_id: int, doc_id: int):
    result = driver.execute_query(
        """
        MATCH (n)
        WHERE n.chunk_id_e <= $chunk_id AND n.doc_id = $doc_id
        RETURN n
        """,
        chunk_id=chunk_id, doc_id=doc_id
    )
    return [record['n'] for record in result.records]

def get_rand_review_question(node_id: str, question_nodes: list = None):
    if question_nodes is None:
        result = driver.execute_query(
            """
            MATCH (n:ReviewQuestion)-[:QUESTION_FOR]->(m)
            WHERE elementId(m) = $node_id
            RETURN n
            """,
            node_id=node_id
        )
        question_nodes = [record['n'] for record in result.records]
    return choice(question_nodes)

import numpy as np
def interpolate(array: list):
    array = np.array(array, dtype=float)
    x = np.arange(len(array))
    nans = np.isnan(array)
    array[nans] = np.interp(x[nans], x[~nans], array[~nans])
    return array.tolist()

def get_chunk_mastery(userid: str, doc_id: int):
    result = driver.execute_query(
        """
        MATCH (n)-[:LAST_REPEATED]->(r:RepetitionState)
        WHERE r.userid = $userid AND n.doc_id = $doc_id
        ORDER BY n.chunk_id_s ASC
        RETURN r, n
        """,
        userid=userid, doc_id=doc_id
    )

    chunk_index_mastery_list = [[] for _ in range(get_max_chunk_order(doc_id) + 1)]
    for record in result.records:
        r = record["r"]
        n = record["n"]
        state = int(r.get("state"))
        for chunk_idx in range(n.get("chunk_id_s"), n.get("chunk_id_e") + 1):
            chunk_index_mastery_list[chunk_idx].append(state)
    chunk_index_mastery = []
    for chunk_idx_mastery in chunk_index_mastery_list:
        val = np.mean(chunk_idx_mastery) if chunk_idx_mastery else 0.0
        chunk_index_mastery.append(val)
    return chunk_index_mastery

from .chunk_maper import chunk_to_page
# Only works for pdf documents
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # This makes it show in terminal
    ]
)

logger = logging.getLogger(__name__)
def get_page_mastery(userid: str, doc_id: int):
    chunk_mastery = get_chunk_mastery(userid, doc_id)
    page_mastery = []
    current_page = 0
    total_mastery = 0
    total_chunks = 0
    logger.info("Computing page mastery: userid=%s doc_id=%s chunk_count=%s", userid, doc_id, len(chunk_mastery))
    for chunk_idx, mastery in enumerate(chunk_mastery):
        total_mastery += mastery
        total_chunks += 1
        try:
            mapped_page = chunk_to_page(chunk_idx, doc_id)
        except Exception as e:
            logger.error(
                "chunk_to_page failed: doc_id=%s chunk_idx=%s current_page=%s total_chunks_in_page=%s error=%s",
                doc_id, chunk_idx, current_page, total_chunks, repr(e), exc_info=True
            )
            raise
        if mapped_page is None:
            logger.error(
                "chunk_to_page returned None: doc_id=%s chunk_idx=%s (no page mapping found)",
                doc_id, chunk_idx
            )
            raise ValueError(f"No page mapping for chunk_idx={chunk_idx} doc_id={doc_id}")
        if mapped_page > current_page:
            page_mastery.append(total_mastery / total_chunks)
            current_page += 1
            total_mastery = 0
            total_chunks = 0
    if total_chunks > 0:
        page_mastery.append(total_mastery / total_chunks)

    # Normalize only if max > 0 to avoid NaN (JSON-incompatible)
    if not page_mastery:
        return []

    page_mastery = np.array(page_mastery, dtype=float)
    max_val = page_mastery.max()
    if max_val > 0:
        page_mastery = page_mastery / max_val
    # else: keep as zeros
    return page_mastery.tolist()
