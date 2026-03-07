import os
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("No GOOGLE_API_KEY found in .env")
    exit(1)

client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})
models = client.models.list()

for i, m in enumerate(models):
    if i > 2: break
    print(f"Model Name: {m.name}")
    print(f"Dir: {dir(m)}")
    methods = getattr(m, 'supported_generation_methods', getattr(m, 'supported_methods', []))
    print(f"Supported Methods: {methods}")
    print("-" * 30)
