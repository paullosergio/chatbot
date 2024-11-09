from datetime import datetime, timezone
from typing import Any, Dict, List

import chromadb


class VectorStore:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path="/root/.cache/chroma/db")
        except Exception as e:
            print(f"Error initializing chromadb client: {e}")
            raise

        # Initialize collections for knowledge base and interactions
        try:
            self.interaction_collection = self.client.get_or_create_collection(
                name="interactions", metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"Error creating collections: {e}")
            raise

    
    async def add_interaction(self, text: str, metadata: Dict[str, Any]) -> None:
        """Adds an interaction to the interactions collection."""
        try:

            metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

            self.interaction_collection.add(
                documents=[text], metadatas=[metadata], ids=[f"i_{hash(text)}"]
            )
        except Exception as e:
            print(f"Error adding interaction: {e}")
            raise


    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Formats the search results to a list of dictionaries."""
        return [
            {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
            for i in range(len(results["ids"][0]))
        ]
