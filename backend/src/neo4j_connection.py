from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv()
# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
driver = GraphDatabase.driver(URI, auth=AUTH)

try:
    driver.verify_connectivity()
    print("✅ Successfully connected to Neo4j!")
except Exception as e:
    print(f"❌ Error connecting to Neo4j: {e}")
