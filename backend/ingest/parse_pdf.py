import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)
import requests
import io
import re
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1024)
def extract_amount_from_pdf(url):
    try:
        import pdfplumber
        # Add headers to bypass simple bot protection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf',
            'Referer': 'https://www.nseindia.com/',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        logger.info(f"Downloading PDF for parsing: {url}")

        # Use a session to persist cookies which sometimes NSE requires
        session = requests.Session()
        # Initial request intentionally has a very short timeout to avoid hanging if the site is slow
        try:
            session.get("https://www.nseindia.com", headers=headers, timeout=2)
        except Exception as e:
            logger.debug(f"Initial NSE prime for PDF failed: {e}")

        # Timeout reduced to 5s to prevent Celery task hanging on unresponsive PDF links
        resp = session.get(url, headers=headers, timeout=5)

        if resp.status_code == 200 and b'%PDF' in resp.content[:10]:
            logger.info(f"Successfully downloaded PDF for parsing: {url}")
            with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                text = ""
                for page in pdf.pages[:5]: # Only check first 5 pages
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"

            # Pre-process text to fix common OCR issues (e.g., 1.551- instead of 1.55/-)
            text = re.sub(r'(\.\d+)1-', r'\1/-', text)

            # Remove "Regulation \d+", "Reg. \d+", "Regulations \d+ and \d+" to prevent false matches
            _clean_text = re.sub(r'Regulations?\s*(?:\d+(?:\s*(?:and|&|,)\s*\d+)*)|Reg\.?\s*\d+', '', text, flags=re.IGNORECASE)

            # Simple regex for dividend amount
            # Look for "dividend" and then quickly find Rs. X
            parts = re.split(r'dividend|int\s*div|fin\s*div', _clean_text, flags=re.IGNORECASE)
            for part in parts[1:]:
                # Only look at the next 300 chars after 'dividend'
                snippet = part[:300]
                _clean = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9)*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', snippet, flags=re.IGNORECASE)

                m = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)\s*(\d+(?:\.\d+)?)', _clean, re.IGNORECASE)
                if m:
                    val = float(m.group(1))
                    if val > 0:
                        return val

            # More specific fallback regexes
            ui_patterns = [
                r'(?:dividend|int\s*div|fin\s*div).*?of\s*(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)\s*(\d+(?:\.\d+)?)',
                r'(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)\s*(\d+(?:\.\d+)?)\s*per\s*share',
                r'(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)\s*(\d+(?:\.\d+)?)\s*/-\s*per\s*share',
                r'(?:dividend|int\s*div|fin\s*div).*?(?:at|@)\s*(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)\s*(\d+(?:\.\d+)?)'
            ]
            for pat in ui_patterns:
                matches2 = re.findall(pat, _clean_text, re.IGNORECASE)
                for m in matches2:
                    val = float(m)
                    if val > 0:
                        return val

    except ImportError:
        logger.debug("pdfplumber not installed, skipping PDF parsing.")
    except Exception as e:
        logger.debug(f"Failed to extract PDF {url}: {e}")
    return None
