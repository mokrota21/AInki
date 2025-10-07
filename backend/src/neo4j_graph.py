from neo4j import GraphDatabase
from neo4j.graph import Node
from dotenv import load_dotenv
import os
from .repetition import RepeatState
from datetime import timezone, datetime
from .neo4j_connection import driver



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

def add_review_question(node_id: str, question: str, question_type: str):
    """
    Create a ReviewQuestion and link it to an existing BookKnowledge node.
    Fails cleanly if the BookKnowledge node doesn't exist.
    """
    query = """
    MATCH (m:BookKnowledge {id: $node_id})
    CREATE (n:ReviewQuestion {type: $type, question: $question})
    CREATE (n)-[:QUESTION_FOR]->(m)
    RETURN n
    """
    result = driver.execute_query(
        query,
        node_id=node_id,
        type=question_type,
        question=question,
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

def get_all_pending(userid: str = None):
    result = driver.execute_query(
        """
        MATCH (n)-[c:LAST_REPEATED]->(r:RepetitionState)
        WHERE r.next_repeat < datetime({year: 9999, month: 1, day: 1, hour: 0, minute: 0, second: 0, millisecond: 0, microsecond: 0, nanosecond: 0, timezone: 'UTC'}) AND (r.userid = $userid OR $userid IS NULL)
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
