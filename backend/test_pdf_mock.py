import datetime
from backend.ingest.parse_pdf import extract_amount_from_pdf
from unittest.mock import patch, MagicMock
import io
import requests

class MockResponse:
    def __init__(self, content, status_code):
        self.content = content
        self.status_code = status_code
        self.headers = {'Content-Type': 'application/pdf'}

# Let's verify that the function runs correctly and handles the tables.
print("Imports successful")
