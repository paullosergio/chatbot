# src/db/vector_store.py
from typing import Any, Dict, List

import chromadb


class VectorStore:
    def __init__(self, host: str, port: int):
        # self.client = chromadb.HttpClient(host=host, port=port)
        self.client = chromadb.PersistentClient(path='/root/.cache/chroma/db')
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge_base", metadata={"hnsw:space": "cosine"}
        )
        self.interaction_collection = self.client.get_or_create_collection(
            name="interactions", metadata={"hnsw:space": "cosine"}
        )

    async def add_knowledge(self, text: str, metadata: Dict[str, Any]) -> None:
        self.knowledge_collection.add(
            documents=[text], metadatas=[metadata], ids=[f"k_{hash(text)}"]
        )

    async def add_interaction(self, text: str, metadata: Dict[str, Any]) -> None:
        self.interaction_collection.add(
            documents=[text], metadatas=[metadata], ids=[f"i_{hash(text)}"]
        )

    async def search_knowledge(self, message: str, n_results: int = 5) -> List[Dict[str, Any]]:
        results = self.knowledge_collection.query(
            query_texts=[message],
            n_results=n_results,
        )
        return self._format_results(results)

    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
            for i in range(len(results["ids"][0]))
        ]
