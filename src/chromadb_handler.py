# chromadb_handler.py


import os
os.environ["CHROMADB_SKIP_SQLITE_CHECK"] = "1"
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from typing import List
from src.embedder import TextEmbedder

class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.embedder = TextEmbedder()
    
    def __call__(self, input: Documents) -> Embeddings:
        return [self.embedder.embed(text).tolist() for text in input]

class ChromaDBHandler:
    def __init__(self):
        self.client = chromadb.PersistentClient()
        # self.client = chromadb.PersistentClient(path="chroma_data", settings={"chroma_db_impl": "duckdb"})
        self.embedding_fn = CustomEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="company_data",
            embedding_function=self.embedding_fn
        )

    def add_documents(self, documents, metadata, ids):
       
        self.collection.add(
            documents=documents,
            metadatas=metadata,
            ids=ids
        )

    def query(self, query_text, n_results=3):
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return " ".join(results['documents'][0])