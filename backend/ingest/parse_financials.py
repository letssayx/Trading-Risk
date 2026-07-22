import logging
import requests
import io
import re
from functools import lru_cache
from bs4 import BeautifulSoup
import pandas as pd
from backend.ingest.nse_lib import NSELib

logger = logging.getLogger(__name__)

def extract_financials_from_xbrl(url):
    """
    Fetches and parses an XBRL XML file to extract the Current Quarter's EPS and Net Profit.
    """
    eps = None
    net_profit = None

    lib = NSELib()
    try:
        logger.info(f"Downloading XBRL for parsing: {url}")
        resp = lib.get(url, use_curl=True)
        if not resp or resp.status_code != 200:
            return eps, net_profit

        soup = BeautifulSoup(resp.content, 'xml')

        # 1. Map contexts
        # We want the context with the shortest duration (Current Quarter) or matching the latest period
        context_map = {}
        for c in soup.find_all('context'):
            cid = c.get('id')
            period = c.find('period')
            if period:
                start = period.find('startDate')
                end = period.find('endDate')
                if start and end:
                    start_date = pd.to_datetime(start.text)
                    end_date = pd.to_datetime(end.text)
                    duration_days = (end_date - start_date).days
                    context_map[cid] = {
                        'start': start_date,
                        'end': end_date,
                        'duration': duration_days
                    }

        if not context_map:
            return eps, net_profit

        # 2. Find the target context (most recent end date, shortest duration roughly 90 days)
        # Sort contexts by endDate descending, then by duration ascending
        sorted_contexts = sorted(context_map.items(), key=lambda x: (x[1]['end'], -x[1]['duration']), reverse=True)

        target_context_id = None
        for cid, info in sorted_contexts:
            # Look for a duration that represents a quarter (roughly 90-95 days)
            if 85 <= info['duration'] <= 95:
                target_context_id = cid
                break

        # If no strict quarter found, just take the most recent one (e.g. YTD or Annual if that's all there is)
        if not target_context_id and sorted_contexts:
            target_context_id = sorted_contexts[0][0]

        if not target_context_id:
            return eps, net_profit

        # 3. Extract ProfitLossForPeriod
        profit_tags = soup.find_all(lambda tag: tag.name and 'ProfitLossForPeriod' in tag.name)
        for tag in profit_tags:
            if tag.get('contextRef') == target_context_id:
                try:
                    val = float(tag.text)
                    if net_profit is None or tag.name.endswith('ProfitLossForPeriod'):
                        # Prefer exactly 'ProfitLossForPeriod' over something like 'ProfitLossForPeriodFromContinuingOperations'
                        net_profit = val
                except:
                    pass

        # 4. Extract EPS
        eps_tags = soup.find_all(lambda tag: tag.name and ('EarningsLossPerShare' in tag.name or 'BasicEarningsLossPerShare' in tag.name))
        for tag in eps_tags:
            if tag.get('contextRef') == target_context_id:
                if 'Basic' in tag.name or 'BasicEarningsLossPerShare' in tag.name or tag.name == 'BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations':
                    try:
                        eps = float(tag.text)
                    except:
                        pass

    except ImportError:
         logger.debug("lxml or bs4 not installed.")
    except Exception as e:
        logger.error(f"Failed to parse XBRL from {url}: {e}")

    return eps, net_profit

@lru_cache(maxsize=128)
def extract_financials_from_pdf(url):
    """
    Fallback method to parse EPS and Net Profit from a PDF attachment.
    """
    eps = None
    net_profit = None
    try:
        import pdfplumber
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf',
            'Referer': 'https://www.nseindia.com/',
        }
        logger.info(f"Downloading PDF for financials parsing: {url}")

        session = requests.Session()
        try: session.get("https://www.nseindia.com", headers=headers, timeout=2)
        except: pass

        resp = session.get(url, headers=headers, timeout=5)
        if resp.status_code == 200 and b'%PDF' in resp.content[:10]:
            with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                for page in pdf.pages[:3]: # Usually in the first few pages
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if not row: continue
                            row_text = [str(cell).strip().lower() for cell in row if cell]

                            # Net Profit
                            if net_profit is None:
                                if any('profit for the period' in c or 'net profit' in c for c in row_text):
                                    # Attempt to find the first numeric value
                                    for cell in row_text:
                                        if 'profit' in cell: continue
                                        m = re.search(r'\(?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*\)?', cell)
                                        if m:
                                            try:
                                                val = float(m.group(1).replace(',', ''))
                                                if '(' in cell or '-' in cell:
                                                    val = -val
                                                net_profit = val
                                                break
                                            except:
                                                pass

                            # EPS
                            if eps is None:
                                if any('earnings per share' in c or 'basic eps' in c or ('basic' in c and 'diluted' in c) for c in row_text):
                                    for cell in row_text:
                                        if 'earning' in cell or 'basic' in cell or 'diluted' in cell: continue
                                        m = re.search(r'\(?\s*(\d+(?:\.\d+)?)\s*\)?', cell)
                                        if m:
                                            try:
                                                val = float(m.group(1))
                                                if '(' in cell or '-' in cell:
                                                    val = -val
                                                eps = val
                                                break
                                            except:
                                                pass
                        if eps is not None and net_profit is not None:
                            break
                    if eps is not None and net_profit is not None:
                        break

    except Exception as e:
        logger.debug(f"Failed to extract financials from PDF {url}: {e}")

    return eps, net_profit
