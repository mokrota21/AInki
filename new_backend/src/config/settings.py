from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from langfuse.openai import AzureOpenAI
# from psycopg2 import connect
from sqlalchemy import create_engine, event
from neo4j import GraphDatabase
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import os
# Import all table models so they register with Base.metadata
from .tables import users, repetitions, docs, chunks, Base, after_create


# Load .env from project root (new_backend/)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
class Settings(BaseSettings):
    # PostgreSQL
    pg_password: str | None = None
    pg_host: str | None = None
    pg_user: str | None = None
    pg_dbname: str | None = None
    pg_url: str | None = None

    # Neo4j
    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None
    neo4j_database: str | None = None
    aura_instanceid: str | None = None
    aura_instancename: str | None = None

    # Langfuse
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None

    # Document Intelligence
    doc_endpoint: str | None = None
    doc_key: str | None = None
    doc_model_id: str | None = None

    # LLM
    llm_provider: str | None = None

    # Azure OpenAI
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    openai_api_version: str | None = None
    azure_openai_deployment_name: str | None = None

    # Internal parameters
    default_reader: str | None = None
    default_chunker: str | None = None
    repetition_ranks_mapping: list | None = None

    @property
    def llm_client(self):
        if self.llm_provider == "azure":
            return AzureOpenAI(
                api_key=self.azure_openai_api_key,
                api_version=self.openai_api_version,
                model=self.azure_openai_deployment_name
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    @property
    def doc_client(self):
        return DocumentIntelligenceClient(self.doc_endpoint, AzureKeyCredential(self.doc_key))

    @property
    def get_neo4j_driver(self):
        driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_username, self.neo4j_password))
        try:
            driver.verify_connectivity()
            print("✅ Successfully connected to Neo4j!")
        except Exception as e:
            print(f"❌ Error connecting to Neo4j: {e}")
        return driver
    
    def get_engine(self):
        engine = create_engine(self.pg_url)
        # Attach event listeners before creating tables
        for table in Base.metadata.tables.values():    
            event.listen(table, "after_create", after_create)
        # Create all tables - this will fire the after_create events
        Base.metadata.create_all(engine)
        return engine
        # return connect(dbname=self.pg_dbname, user=self.pg_user, host=self.pg_host, password=self.pg_password)

settings = Settings()