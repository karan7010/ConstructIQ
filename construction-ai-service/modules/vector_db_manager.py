import chromadb
from chromadb.utils import embedding_functions
import os

class VectorDBManager:
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="construction_knowledge",
            embedding_function=self.embedding_fn
        )

    def add_documents(self, documents: list, metadatas: list, ids: list):
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text: str, n_results: int = 3):
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

db_manager = VectorDBManager()
