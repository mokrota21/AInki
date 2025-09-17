from neo4j import GraphDatabase
from neo4j.graph import Node
from dotenv import load_dotenv
import os
load_dotenv()
# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = "neo4j+s://e5703e68.databases.neo4j.io"
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

driver = GraphDatabase.driver(URI, auth=AUTH)

def add_definition(name: str, doc_id: int, chunk_id: int, idx_s: int, idx_e: int):
    """
    Add definition to the NEO4j graph.
    name: Name of the definition;
    doc_id: id of document it is taken from;
    chunk_id: id of chunk it is taken from (chunk of corresponding document);
    idx_s: index of character in chunk where definition starts;
    idx_e: index of character in chunk where definition ends (not including);
    """
    assert idx_e >= idx_s

    summary = driver.execute_query(
        "CREATE (d:Definition {name: $name, doc_id: $doc_id, chunk_id: $chunk_id, idx_s: $idx_s, idx_e: $idx_e}) RETURN d",
        name=name, doc_id=doc_id, chunk_id=chunk_id, idx_s=idx_s, idx_e=idx_e
    )
    return summary.records[0]["d"]

def add_property(name: str, doc_id: int, chunk_id: int, idx_s: int, idx_e: int):
    """
    Add property to the NEO4j graph.
    name: Name of the property;
    doc_id: id of document it is taken from;
    chunk_id: id of chunk it is taken from (chunk of corresponding document);
    idx_s: index of character in chunk where property starts;
    idx_e: index of character in chunk where property ends (not including);
    """
    assert idx_e >= idx_s

    summary = driver.execute_query(
        "CREATE (p:Property {name: $name, doc_id: $doc_id, chunk_id: $chunk_id, idx_s: $idx_s, idx_e: $idx_e}) RETURN p",
        name=name, doc_id=doc_id, chunk_id=chunk_id, idx_s=idx_s, idx_e=idx_e
    )
    return summary.records[0]["p"]

def add_theorem(name: str, doc_id: int, chunk_id: int, idx_s: int, idx_e: int):
    """
    Add theorem to the NEO4j graph.
    name: Name of the theorem;
    doc_id: id of document it is taken from;
    chunk_id: id of chunk it is taken from (chunk of corresponding document);
    idx_s: index of character in chunk where theorem starts;
    idx_e: index of character in chunk where theorem ends (not including);
    """
    assert idx_e >= idx_s

    summary = driver.execute_query(
        "CREATE (t:Theorem {name: $name, doc_id: $doc_id, chunk_id: $chunk_id, idx_s: $idx_s, idx_e: $idx_e}) RETURN t",
        name=name, doc_id=doc_id, chunk_id=chunk_id, idx_s=idx_s, idx_e=idx_e
    )
    return summary.records[0]["t"]

def add_relation(node1: Node, node2: Node):
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
        id1 = node1.id, id2 = node2.id
    )
    return summary.records[0]["r"]
