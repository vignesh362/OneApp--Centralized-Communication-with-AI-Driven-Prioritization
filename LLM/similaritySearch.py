from qdrant_client import QdrantClient
from createEmbeddings import creatEmbedding
# Configuration
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "Data_embeddings"

# Initialize Qdrant client
client = QdrantClient(QDRANT_URL)

def similarity_search(query_vector, top_k=5):
    """
    Perform similarity search in the Qdrant vector database.
    
    Args:
        query_vector (list): The query vector to search for.
        top_k (int): Number of most similar vectors to retrieve.
    
    Returns:
        list: A list of search results containing IDs, scores, and payloads.
    """
    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k
        )
        # Format the results
        formatted_results = [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]
        return formatted_results
    except Exception as e:
        print(f"Error during similarity search: {e}")
        return []

# Example Usage
if __name__ == "__main__":
    # Replace this with your actual query vector
    txt=creatEmbedding("All you have to do is choose which beverage to enjoy first. (We'd probably go for a Chai Latte. Wait, maybe an Organic Iced Mocha? No! How about Cold Brew? This is getting tricky, right?) coffee cup Savor up to 5 Barista-crafted drinks per day. Redeem once every 30 minutes (any size, any type of milk or plant-based milk, plus 1 additional flavor syrup or espresso shot). customer This subscription is personal and can’t be shared. delivery Can be redeemed at participating US locations. This subscription isn’t available on Grubhub, DoorDash, Uber Eats, or at non-participating locations. Non-participating locations: Westwood, Studio City, Drexel University, University of Chicago, University of Pennsylvania, Vince Lombardi.")
    top_k = 5  # Number of results to fetch

    # Perform similarity search
    search_results = similarity_search(txt, top_k=top_k)

    # Display results
    if search_results:
        print("Similarity Search Results:")
        for result in search_results:
            print(f"ID: {result['id']}")
            print(f"Score: {result['score']}")
            print(f"Payload: {result['payload']}")
            print("-" * 50)
    else:
        print("No results found.")
