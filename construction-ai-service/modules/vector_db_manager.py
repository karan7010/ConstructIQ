import chromadb
from chromadb.utils import embedding_functions
import os

class VectorDBManager:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self._client = None
        self._embedding_fn = None
        self._collection = None

    @property
    def client(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self.persist_directory)
        return self._client

    @property
    def embedding_fn(self):
        if self._embedding_fn is None:
            # This is the heavy operation that we lazily load
            self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        return self._embedding_fn

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name="construction_knowledge",
                embedding_function=self.embedding_fn
            )
        return self._collection

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

# Global singleton accessor
_manager_instance = None

def get_db_manager():
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = VectorDBManager()
    return _manager_instance
