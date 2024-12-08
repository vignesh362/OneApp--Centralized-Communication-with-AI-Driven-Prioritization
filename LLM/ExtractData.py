from pymongo import MongoClient
import logging
from qdrantStorage import QdrantEmbeddingStorage
# MongoDB connection URI
MONGO_URI = "mongodb://localhost:27017"

# Connect to MongoDB
client = MongoClient(MONGO_URI)

# Select database and collection
db = client["email_data"]
collection = db["emails"]

# Fetch all documents
documents = collection.find()
storage = QdrantEmbeddingStorage()


# Print all fields (columns) separately
for doc in documents:
    print(doc)
    text_data = doc['subject']+" "+doc['body']
    metadata = {
        "source": "gmail",
        "date": doc['received_date'],
        "description": doc
    }

    success = storage.store_embedding(text_data, metadata)
    if success:
        logging.info("Embedding successfully stored.")
    else:
        logging.error("Failed to store embedding.")
    print("-" * 50)  # Separator for each document

# Close the connection
client.close()