import os
import requests
from typing import List

def get_bge_m3_embedding(text: str) -> List[float]:
    """
    Calls the HuggingFace Inference API to get the 1024-dimensional
    embedding for the provided text using BAAI/bge-m3.
    """
    api_url = "https://api-inference.huggingface.co/models/BAAI/bge-m3"
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        print("WARNING: HUGGINGFACE_API_KEY is not set. Using dummy embedding for dev.")
        return [0.0] * 1024

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": text}

    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Failed to get embedding. Status {response.status_code}: {response.text}")
        return [0.0] * 1024

    data = response.json()
    # Handle possible formats returned by HuggingFace API
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], list):
             return data[0]
        return data
    elif isinstance(data, dict) and "embeddings" in data:
        return data["embeddings"][0] if isinstance(data["embeddings"][0], list) else data["embeddings"]

    return [0.0] * 1024
