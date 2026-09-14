import re

with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# Add python-dotenv loading right before grabbing groq_key
patch = """
            # Ensure dotenv is reloaded dynamically since Celery might have booted before the key was saved
            try:
                from dotenv import load_dotenv
                load_dotenv(override=True)
            except ImportError:
                pass

            groq_key = os.getenv("GROQ_API_KEY")"""

content = content.replace('groq_key = os.getenv("GROQ_API_KEY")', patch.strip())

with open('backend/ingest/tasks.py', 'w') as f:
    f.write(content)
