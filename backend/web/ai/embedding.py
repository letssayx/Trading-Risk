import os
import httpx

# BAAI/bge-m3 on HuggingFace Inference API
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/BAAI/bge-m3"

async def get_bge_m3_embedding(text: str) -> list[float]:
    """
    Fetches a 1024-dimensional embedding for the given text.
    Uses HuggingFace Inference API.
    """
    api_key = os.getenv("HF_TOKEN")
    if not api_key:
        print("Warning: HF_TOKEN not set. Returning zero vector.")
        return [0.0] * 1024

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": text}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(HF_API_URL, headers=headers, json=payload, timeout=10.0)

        if response.status_code == 200:
            result = response.json()
            # The result is typically a list of floats or a list of lists of floats depending on the pipeline
            if isinstance(result, list):
                if len(result) > 0 and isinstance(result[0], list):
                     return result[0][:1024] # Flatten and truncate if needed, BGE-M3 should be 1024
                return result[:1024]
            return [0.0] * 1024
        else:
            print(f"HF API Error: {response.status_code} - {response.text}")
            return [0.0] * 1024
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return [0.0] * 1024
