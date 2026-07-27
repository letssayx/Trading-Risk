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
    amount = None
    record_date = None
    div_type = None
    agm_date = None
    try:
        import pdfplumber
        import pandas as pd
        # Add headers to bypass simple bot protection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf',
            'Referer': 'https://www.nseindia.com/',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        logger.debug(f"Downloading PDF for parsing: {url}")

        from curl_cffi import requests as curl_requests
        session = curl_requests.Session(impersonate="chrome110")
        try:
            session.get("https://www.nseindia.com", headers=headers, timeout=2)
        except Exception as e:
            logger.debug(f"Initial NSE prime for PDF failed: {e}")

        # Timeout reduced to 5s to prevent Celery task hanging on unresponsive PDF links
        resp = session.get(url, headers=headers, timeout=5)

        if resp.status_code == 200 and b'%PDF' in resp.content[:10]:
            logger.debug(f"Successfully downloaded PDF for parsing: {url}")
            with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                text = ""
                tables = []
                for page in pdf.pages[:5]: # Only check first 5 pages
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)

            # Record Date extraction
            if "record date" in text.lower():
                rd_patterns = [
                    r'record\s*date[^\n]*?((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\s*,?\s*\d{4})',
                    r'record\s*date[^\n]*?(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})',
                    r'record\s*date[^\n]*?(\d{1,2}\s*[-/]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*[-/]\s*\d{4})',
                    r'record\s*date[^\n]*?(\d{1,2}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{4})'
                ]
                for p in rd_patterns:
                    m = re.search(p, text, re.IGNORECASE)
                    if m:
                        record_date_str = m.group(1).replace('\n', ' ').strip()
                        try:
                            record_date = pd.to_datetime(record_date_str).strftime('%d-%b-%Y')
                            break
                        except Exception:
                            record_date = record_date_str
                            break

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

                # Ensure we strictly look for currency or @ symbols, to avoid matching stray numbers like 'on 27th April' where 'n 27' is found
                m = re.search(r'(?:rs\.?|re\.?|rupees|inr|\u20b9|~|nS?\.|n\s*\.)\s*(\d+(?:\.\d+)?)', _clean, re.IGNORECASE)
                m2 = re.search(r'@\s*(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)?\s*(\d+(?:\.\d+)?)\s*(?:/-|per\s+share|per\s+equity)', _clean, re.IGNORECASE)
                match = m or m2
                if match:
                    val = float(match.group(1))
                    if val > 0 and val < 1000: # sanity check to avoid year matching
                        amount = val
                        break


            # AGM Date extraction from PDF
            agm_patterns = [
                r'(?:annual general meeting|agm).*?to be held on.*?\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b',
                r'(?:annual general meeting|agm).*?scheduled.*?on.*?\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b',
                r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b.*?(?:annual general meeting|agm)',
                r'(?:agm|annual general meeting).*?\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b'
            ]
            for pat in agm_patterns:
                agm_m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
                if agm_m:
                    agm_date_str = agm_m.group(1).replace('\n', ' ').strip()
                    try:
                        agm_date = pd.to_datetime(agm_date_str).strftime('%Y-%m-%d')
                        break
                    except Exception:
                        pass

            # Dividend type extraction from PDF
            if re.search(r'\b(?:1st|first|2nd|second|3rd|third|4th|fourth)?\s*interim\s+dividend\b', text, re.IGNORECASE):
                div_type = 'Interim'
            elif re.search(r'\bfinal\s+dividend\b', text, re.IGNORECASE):
                div_type = 'Final'
            elif re.search(r'\bspecial\s+dividend\b', text, re.IGNORECASE):
                div_type = 'Special'

            if amount is None:
                # More specific fallback regexes
                ui_patterns = [
                    r'(?:dividend|int\s*div|fin\s*div).*?of\s*(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)\s*(\d+(?:\.\d+)?)',
                    r'(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)\s*(\d+(?:\.\d+)?)\s*per\s*share',
                    r'(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)\s*(\d+(?:\.\d+)?)\s*/-\s*per\s*share',
                    r'(?:dividend|int\s*div|fin\s*div).*?(?:at|@)\s*(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)\s*(\d+(?:\.\d+)?)'
                ]
                for pat in ui_patterns:
                    matches2 = re.findall(pat, _clean_text, re.IGNORECASE)
                    found = False
                    for m in matches2:
                        val = float(m)
                        if val > 0 and val < 1000:
                            amount = val
                            found = True
                            break
                    if found:
                        break

            # Fallback 3: Try Tables
            if (amount is None or record_date is None) and tables:
                for table in tables:
                    for row in table:
                        row_text = [str(cell).strip().lower() for cell in row if cell]

                        # Amount extraction from table
                        if amount is None and any('dividend' in cell for cell in row_text):
                            for cell in row_text:
                                if 'dividend' in cell: continue
                                m = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9|~|nS?\.?|n\s*\.?)\s*(\d+(?:\.\d+)?)', cell, re.IGNORECASE)
                                if m:
                                    val = float(m.group(1))
                                    if val > 0:
                                        amount = val
                                        break
                                m2 = re.match(r'^\s*(\d+(?:\.\d+)?)\s*$', cell)
                                if m2:
                                    val = float(m2.group(1))
                                    if val > 0:
                                        amount = val
                                        break

                        # Record date extraction from table
                        if record_date is None and any('record date' in cell for cell in row_text):
                            for cell in row_text:
                                if 'record date' in cell: continue
                                m = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\s*,?\s*\d{4})', cell, re.IGNORECASE)
                                if m:
                                    record_date_str = m.group(1).replace('\n', ' ').strip()
                                    try:
                                        record_date = pd.to_datetime(record_date_str).strftime('%d-%b-%Y')
                                        break
                                    except Exception:
                                        pass
                                m2 = re.search(r'(\d{1,2}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{4})', cell, re.IGNORECASE)
                                if m2:
                                    record_date_str = m2.group(1).replace('\n', ' ').strip()
                                    try:
                                        record_date = pd.to_datetime(record_date_str, format="%d-%m-%Y").strftime('%d-%b-%Y')
                                        break
                                    except Exception:
                                        try:
                                            record_date = pd.to_datetime(record_date_str).strftime('%d-%b-%Y')
                                            break
                                        except Exception:
                                            pass
                                m3 = re.search(r'(\d{1,2}\s*[-/]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*[-/]\s*\d{4})', cell, re.IGNORECASE)
                                if m3:
                                    record_date_str = m3.group(1).replace('\n', ' ').strip()
                                    try:
                                        record_date = pd.to_datetime(record_date_str).strftime('%d-%b-%Y')
                                        break
                                    except Exception:
                                        pass
                                m4 = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})', cell, re.IGNORECASE)
                                if m4:
                                    record_date_str = m4.group(1).replace('\n', ' ').strip()
                                    try:
                                        record_date = pd.to_datetime(record_date_str).strftime('%d-%b-%Y')
                                        break
                                    except Exception:
                                        pass

                    if amount is not None and record_date is not None:
                        break

    except ImportError:
        logger.debug("pdfplumber not installed, skipping PDF parsing.")
    except Exception as e:
        logger.debug(f"Failed to extract PDF {url}: {e}")
    return amount, record_date, div_type, agm_date
