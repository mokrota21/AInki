from neo4j import GraphDatabase
from neo4j.graph import Node
from dotenv import load_dotenv
import os
from .repetition import RepeatState
from datetime import timezone, datetime

# dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv()
# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("✅ Successfully connected to Neo4j!")

tz = timezone.utc

driver = GraphDatabase.driver(URI, auth=AUTH)

def add_definition(name: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add definition to the NEO4j graph.
    name: Name of the definition;
    doc_id: id of document it is taken from;
    chunk_id_s: starting chunk id where definition begins;
    chunk_id_e: ending chunk id where definition ends;
    """
    assert chunk_id_e >= chunk_id_s

    summary = driver.execute_query(
        "CREATE (d:Definition {name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}) RETURN d",
        name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["d"]

def add_property(name: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add property to the NEO4j graph.
    name: Name of the property;
    doc_id: id of document it is taken from;
    chunk_id_s: starting chunk id where property begins;
    chunk_id_e: ending chunk id where property ends;
    """
    assert chunk_id_e >= chunk_id_s

    summary = driver.execute_query(
        "CREATE (p:Property {name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}) RETURN p",
        name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["p"]

def add_theorem(name: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add theorem to the NEO4j graph.
    name: Name of the theorem;
    doc_id: id of document it is taken from;
    chunk_id_s: starting chunk id where theorem begins;
    chunk_id_e: ending chunk id where theorem ends;
    """
    assert chunk_id_e >= chunk_id_s

    summary = driver.execute_query(
        "CREATE (t:Theorem {name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}) RETURN t",
        name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["t"]

def add_lemma(name: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add lemma to the NEO4j graph.
    name: Name of the lemma;
    doc_id: id of document it is taken from;
    chunk_id_s: starting chunk id where lemma begins;
    chunk_id_e: ending chunk id where lemma ends;
    """
    assert chunk_id_e >= chunk_id_s

    summary = driver.execute_query(
        "CREATE (l:Lemma {name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}) RETURN l",
        name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["l"]

def add_axiom(name: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add axiom to the NEO4j graph.
    name: Name of the axiom;
    doc_id: id of document it is taken from;
    chunk_id_s: starting chunk id where axiom begins;
    chunk_id_e: ending chunk id where axiom ends;
    """
    assert chunk_id_e >= chunk_id_s

    summary = driver.execute_query(
        "CREATE (a:Axiom {name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}) RETURN a",
        name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["a"]

def add_corollary(name: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add corollary to the NEO4j graph.
    name: Name of the corollary;
    doc_id: id of document it is taken from;
    chunk_id_s: starting chunk id where corollary begins;
    chunk_id_e: ending chunk id where corollary ends;
    """
    assert chunk_id_e >= chunk_id_s

    summary = driver.execute_query(
        "CREATE (c:Corollary {name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}) RETURN c",
        name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["c"]

def add_conjecture(name: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add conjecture to the NEO4j graph.
    name: Name of the conjecture;
    doc_id: id of document it is taken from;
    chunk_id_s: starting chunk id where conjecture begins;
    chunk_id_e: ending chunk id where conjecture ends;
    """
    assert chunk_id_e >= chunk_id_s

    summary = driver.execute_query(
        "CREATE (c:Conjecture {name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}) RETURN c",
        name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["c"]

def add_example(name: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add example to the NEO4j graph.
    name: Name of the example;
    doc_id: id of document it is taken from;
    chunk_id_s: starting chunk id where example begins;
    chunk_id_e: ending chunk id where example ends;
    """
    assert chunk_id_e >= chunk_id_s

    summary = driver.execute_query(
        "CREATE (e:Example {name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}) RETURN e",
        name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["e"]

def add_proof(name: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add proof to the NEO4j graph.
    name: Name of the proof;
    doc_id: id of document it is taken from;
    chunk_id_s: starting chunk id where proof begins;
    chunk_id_e: ending chunk id where proof ends;
    """
    assert chunk_id_e >= chunk_id_s

    summary = driver.execute_query(
        "CREATE (p:Proof {name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}) RETURN p",
        name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["p"]

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

def add_other(name: str, doc_id: int, chunk_id_s: int, chunk_id_e: int):
    """
    Add other information to the NEO4j graph.
    name: Name of the other information;
    doc_id: id of document it is taken from;
    chunk_id_s: starting chunk id where implicit knowledge begins;
    chunk_id_e: ending chunk id where implicit knowledge ends;
    """
    assert chunk_id_e >= chunk_id_s

    summary = driver.execute_query(
        "CREATE (i:ImplicitKnowledge {name: $name, doc_id: $doc_id, chunk_id_s: $chunk_id_s, chunk_id_e: $chunk_id_e}) RETURN i",
        name=name, doc_id=doc_id, chunk_id_s=chunk_id_s, chunk_id_e=chunk_id_e
    )
    return summary.records[0]["i"]

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

def get_all_pending(userid: str):
    result = driver.execute_query(
        """
        MATCH (n)-[c:LAST_REPEATED]->(r:RepetitionState)
        WHERE r.next_repeat < datetime({year: 9999, month: 1, day: 1, hour: 0, minute: 0, second: 0, millisecond: 0, microsecond: 0, nanosecond: 0, timezone: 'UTC'}) AND r.userid = $userid
        RETURN n, c, r
        """,
        userid=userid
    )
    return result.records
