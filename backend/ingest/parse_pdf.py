import requests
import io
import re
import logging

logger = logging.getLogger(__name__)

def extract_amount_from_pdf(url):
    try:
        import pdfplumber
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                text = ""
                for page in pdf.pages[:3]: # Only check first 3 pages
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"

            # Simple regex for dividend amount
            # Look for "dividend" and then quickly find Rs. X
            parts = re.split(r'(?i)dividend', text)
            for part in parts[1:]:
                # Only look at the next 100 chars after 'dividend'
                snippet = part[:150]
                _clean = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9)*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', snippet, flags=re.IGNORECASE)

                m = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean, re.IGNORECASE)
                if m:
                    val = float(m.group(1))
                    if val > 0:
                        return val

            # More specific fallback regexes
            ui_patterns = [
                r'dividend.*?of\s*(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)',
                r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)\s*per\s*share',
                r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)\s*/-\s*per\s*share',
                r'dividend.*?(?:at|@)\s*(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)'
            ]
            for pat in ui_patterns:
                matches2 = re.findall(pat, text, re.IGNORECASE)
                for m in matches2:
                    val = float(m)
                    if val > 0:
                        return val

    except ImportError:
        logger.debug("pdfplumber not installed, skipping PDF parsing.")
    except Exception as e:
        logger.debug(f"Failed to extract PDF {url}: {e}")
    return None
