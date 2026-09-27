from datetime import date

import psycopg2
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGEngine, PGVectorStore
from pgvector.psycopg2 import register_vector
from pydantic.v1 import BaseSettings


class Config(BaseSettings):
    user: str
    password: str
    host: str
    database: str
    port: int

    class Config:
        env_file = ".env"


class Database:
    def __init__(self) -> None:
        self.config = Config()
        self.conn = psycopg2.connect(
            host=self.config.host,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            port=self.config.port,
        )
        self.cur = self.conn.cursor()
        register_vector(self.conn)
        self.connection_string = (
            f"postgresql+asyncpg://{self.config.user}:{self.config.password}"
            f"@{self.config.host}:{self.config.port}/{self.config.database}"
        )
        self.embedder = OllamaEmbeddings(model="embeddinggemma:latest")
        self.create_table()
        self.store = PGVectorStore.create_sync(
            engine=PGEngine.from_connection_string(url=self.connection_string),
            embedding_service=self.embedder,
            table_name="vectors",
            id_column="id",
            content_column="description",
            embedding_column="embedding",
            metadata_columns=["label", "url", "tags", "document_date"],
        )

    # This embedding model which I use is 768 dimensions. Choose different - find size.
    def create_table(self) -> None:
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vectors (
                id bigserial primary key,
                label text,
                url text,
                description text,
                tags text[],
                document_date date,
                embedding vector(768)
            );
            """
        )
        self.conn.commit()

    def insert_page(
        self,
        label: str,
        url: str,
        description: str,
        tags: list[str],
        document_date: date,
    ) -> None:

        if label is not None:
            self.cur.execute(
                """
                SELECT COUNT(*) FROM vectors WHERE label = %s
                """,
                (label,),
            )
            count = self.cur.fetchone()[0]
            if count > 0:
                print("Duplicate label found")
                return

        embedding_text = f"{label}\n{url}\n{description}\n{tags}\n{document_date}"

        embedding = self.embedder.embed_query(embedding_text)
        print("Inserting into database: ", label)
        self.cur.execute(
            """
            INSERT INTO vectors (label, url, description, tags, document_date, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (label, url, description, tags, document_date, embedding),
        )
        self.conn.commit()

    def search(self, query: str, k: int = 4) -> list[dict[str, str]]:
        print("Database searching for: ", query)
        embedding = self.embedder.embed_query(query)
        print("Query embedding:", embedding[:5])
        documents_distances: list[tuple[Document, float]] = (
            self.store.similarity_search_with_score_by_vector(embedding, k=k)
        )
        documents = [document for document, _ in documents_distances]

        try:
            for document, distance in documents_distances:
                print("Document id: ", document.id, "Document label: ", document.metadata.get("label"), "Distance: ", distance)
        except IndexError as e:
            print("No documents found", e.args)
        

        return [
            {
                "label": str(document.metadata.get("label") or ""),
                "url": str(document.metadata.get("url") or ""),
                "description": document.page_content,
                "document_date": str(document.metadata.get("document_date") or ""),
            }
            for document in documents
        ]


database = Database()
