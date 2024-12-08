import requests
import uuid
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from createEmbeddings import creatEmbedding
import bson

class QdrantEmbeddingStorage:
    def __init__(self, qdrant_url="http://localhost:6333", collection_name="Data_embeddings", vector_size=384):
        logging.basicConfig(level=logging.INFO)
        self.qdrant_client = QdrantClient(qdrant_url)
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._initialize_collection()

    def _initialize_collection(self):
        if not self.qdrant_client.collection_exists(self.collection_name):
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )

    def serialize_metadata(self, metadata):
        """
        Recursively serialize metadata to ensure all fields are JSON-serializable.
        """
        def serialize_value(value):
            if isinstance(value, bson.ObjectId):
                return str(value)
            if isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            if isinstance(value, list):
                return [serialize_value(v) for v in value]
            return value

        return serialize_value(metadata)

    def store_embedding(self, text, metadata):
        try:
            # Serialize metadata
            serialized_metadata = self.serialize_metadata(metadata)

            # Generate embedding
            embedding = creatEmbedding(text)
            if not embedding:
                logging.error("Failed to generate embedding for text: %s", text)
                return False

            # Create a unique point ID
            point_id = str(uuid.uuid4())

            # Store the embedding in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=serialized_metadata
                    )
                ]
            )
            logging.info(f"Stored text '{text}' with ID {point_id}")
            return True
        except Exception as e:
            logging.error("Error while storing embedding: %s", e)
            return False

# Example usage
if __name__ == "__main__":
    storage = QdrantEmbeddingStorage()
    
    text_data = "This is a sample text for embedding storage."
    metadata = {
        "source": "gmail",
        "date": "2024-12-07",
        "description": {
            "_id": bson.ObjectId(),
            "details": "Sample description"
        }
    }

    success = storage.store_embedding(text_data, metadata)
    if success:
        logging.info("Embedding successfully stored.")
    else:
        logging.error("Failed to store embedding.")
