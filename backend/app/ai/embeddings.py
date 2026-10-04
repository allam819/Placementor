import os
import requests

def generate_embedding(text: str) -> list[float]:
    """Generates a 384-dimensional embedding vector via HuggingFace API to save RAM."""
    # Use HF Inference API for all-MiniLM-L6-v2
    api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
    headers = {"Content-Type": "application/json"}
    
    # Optional: Use HF token if available in env to avoid rate limits
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        
    try:
        response = requests.post(api_url, headers=headers, json={"inputs": text}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Embedding API failed: {e}")
        # Return a zero vector of 384 dims as a safe fallback if API is down
        return [0.0] * 384
