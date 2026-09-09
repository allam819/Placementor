from sentence_transformers import SentenceTransformer

# Load model globally to avoid reloading on every request
# all-MiniLM-L6-v2 is small, fast, and generates 384-dimensional embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str) -> list[float]:
    """Generates a 384-dimensional embedding vector for the given text."""
    embedding = model.encode(text)
    return embedding.tolist()
