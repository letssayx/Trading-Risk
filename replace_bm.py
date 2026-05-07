import re

with open('backend/ingest/nse_lib.py', 'r') as f:
    content = f.read()

# I will write a custom python script to modify the content of `get_board_meetings` to fetch the global announcements first.
# By passing it as a raw string to the file, and then doing normal string replace.

old_logic = """    def get_board_meetings(self, trade_date: date) -> pd.DataFrame:
        \"\"\"Get Board Meetings.\"\"\"
        from datetime import timedelta
        from_date_str = trade_date.strftime("%d-%m-%Y")
        to_date_str = (trade_date + timedelta(days=180)).strftime("%d-%m-%Y")
        url = f"{self.BASE_URL}/api/corporate-board-meetings?index=equities&from_date={from_date_str}&to_date={to_date_str}"

        resp = self.get(url)
        if resp is None:
            return pd.DataFrame()

        if resp.status_code == 200:
            try:
                # The JSON endpoint actually respects historical dates
                data = resp.json()
                if not data:
                     return pd.DataFrame()

                # Fetch XBRL dividends for matching symbols
                enriched_data = []
                import xml.etree.ElementTree as ET

                # Cache databank calls per symbol so we don't repeat API hits for the same stock
                ca_databank_cache = {}

                # Fetch announcements for all symbols in this batch at once to avoid hitting the API N times
                # If there are too many, this might fail, so we will only fetch for those explicitly mentioning dividend.
                # To avoid N+1 queries, we only query for rows that explicitly have "dividend"
                for item in data:
                    item['EXTRACTED_DIVIDEND_AMOUNT'] = None
                    item['EXTRACTED_DIVIDEND_TYPE'] = None

                    purpose = str(item.get('bm_purpose', '')).lower()
                    desc = str(item.get('bm_desc', '')).lower()

                    # We are only interested if dividend is explicitly mentioned. 'financial results' alone creates too many false positive API calls.
                    if 'dividend' in purpose or 'dividend' in desc:
                        symbol = item.get('bm_symbol')
                        if symbol:
                            # Instead of from/to date spanning 180 days which makes parsing hundreds of rows,
                            # limit search to the exact meeting date or closely surrounding dates.
                            meeting_date_str = item.get('bm_date')
                            if meeting_date_str:
                                ann_url = f"{self.BASE_URL}/api/corporate-announcements?index=equities&symbol={symbol}&from_date={meeting_date_str}&to_date={meeting_date_str}"
                                try:
                                    # Use self.get(..., use_curl=True) to bypass 403 blocks from Akamai bot protection.
                                    # Since use_curl handles the request via curl_cffi, we need to pass a shorter timeout locally.
                                    # To prevent hanging the celery task, we explicitly use requests.get if use_curl fails, but with short timeout.
                                    try:
                                        import curl_cffi.requests as cffi_requests
                                        ann_resp = cffi_requests.get(ann_url, impersonate="chrome110", timeout=3, headers=self.HEADERS)
                                    except:
                                        import requests as std_requests
                                        try:
                                            ann_resp = std_requests.get(ann_url, timeout=3, headers=self.HEADERS)
                                        except:
                                            ann_resp = None

                                    if ann_resp and ann_resp.status_code == 200:
                                        ann_data = ann_resp.json()

                                        # Parse text fallbacks
                                        import re
                                        found_amount = None
                                        found_record_date = None

                                        for ann in ann_data:
                                            if not isinstance(ann, dict): continue
                                            desc = str(ann.get('desc', '')).lower()
                                            text = str(ann.get('attchmntText', ''))

                                            if not found_amount and ('outcome' in desc or 'dividend' in desc):
                                                match = re.search(r'(?:rs\.?|re\.?|rupees?|inr)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
                                                if match:
                                                    found_amount = float(match.group(1))

                                            if not found_record_date and ('record date' in desc or 'dividend' in desc):
                                                match = re.search(r'(?:is|on)\s+(\d{1,2}[-\s][A-Za-z]{3,}[-\s]\d{2,4})', text, re.IGNORECASE)
                                                if match:
                                                    found_record_date = match.group(1)

                                        if found_amount:
                                            item['EXTRACTED_DIVIDEND_AMOUNT'] = found_amount
                                            item['EXTRACTED_DIVIDEND_TYPE'] = 'Final'
                                        if found_record_date:
                                            item['EXTRACTED_RECORD_DATE'] = found_record_date

                                        # Also attempt XBRL as primary if available
                                        for ann in ann_data:
                                            if isinstance(ann, dict) and ann.get('hasXbrl') and ('outcome' in str(ann.get('desc')).lower() or 'dividend' in str(ann.get('desc')).lower()):
                                                xbrl_api = f"{self.BASE_URL}/api/corporate-announcements-xbrl?seq_id={ann.get('seq_id')}"
                                                try:
                                                    xbrl_resp = cffi_requests.get(xbrl_api, impersonate="chrome110", timeout=3, headers=self.HEADERS)
                                                except:
                                                    import requests as std_requests
                                                    try:
                                                        xbrl_resp = std_requests.get(xbrl_api, timeout=3, headers=self.HEADERS)
                                                    except:
                                                        xbrl_resp = None

                                                if xbrl_resp and xbrl_resp.status_code == 200:
                                                    try:
                                                        xbrl_json = xbrl_resp.json()
                                                        if isinstance(xbrl_json, list) and len(xbrl_json) > 0:
                                                            xml_url = xbrl_json[0].get('xbrl')
                                                            if xml_url:
                                                                try:
                                                                    xml_resp = cffi_requests.get(xml_url, impersonate="chrome110", timeout=3, headers=self.HEADERS)
                                                                except:
                                                                    import requests as std_requests
                                                                    try:
                                                                        xml_resp = std_requests.get(xml_url, timeout=3, headers=self.HEADERS)
                                                                    except:
                                                                        xml_resp = None

                                                                if xml_resp and xml_resp.status_code == 200:
                                                                    root = ET.fromstring(xml_resp.content)
                                                                    amount = 0.0
                                                                    div_type = 'Final'
                                                                    for elem in root.iter():
                                                                        tag = elem.tag.split('}')[-1]
                                                                        if tag in [
                                                                            'RateOfFinalDividendRecommendedPerEquityShare',
                                                                            'RateOfInterimDividendDeclaredPerEquityShare',
                                                                            'RateOfDividendRecommendedPerEquityShare',
                                                                            'RateOfSpecialDividendDeclaredPerEquityShare',
                                                                            'DividendPerShare'
                                                                        ]:
                                                                            try:
                                                                                amount += float(elem.text)
                                                                            except:
                                                                                pass
                                                                        if tag == 'TypeOfDividend' and elem.text:
                                                                            div_type = elem.text
                                                                    if amount > 0:
                                                                        # Override fallback with exact XBRL amount
                                                                        item['EXTRACTED_DIVIDEND_AMOUNT'] = amount
                                                                        item['EXTRACTED_DIVIDEND_TYPE'] = div_type
                                                                        break
                                                    except ValueError:
                                                        pass
                                except Exception as e:
                                    logger.error(f"Failed to fetch XBRL for {symbol}: {e}")

                                try:
                                    # Final Fallback: Fetch from Corporate Actions Data Bank if still missing
                                    if not item.get('EXTRACTED_DIVIDEND_AMOUNT'):
                                        if symbol not in ca_databank_cache:
                                            ca_url = f"{self.BASE_URL}/api/corporates-corporateActions?index=equities&symbol={symbol}"
                                            try:
                                                # Reduce timeout drastically for the fallback to prevent hanging the celery task
                                                ca_resp = cffi_requests.get(ca_url, impersonate="chrome110", timeout=3, headers=self.HEADERS)
                                            except:
                                                import requests as std_requests
                                                try:
                                                    ca_resp = std_requests.get(ca_url, timeout=3, headers=self.HEADERS)
                                                except:
                                                    ca_resp = None

                                            if ca_resp and ca_resp.status_code == 200:
                                                try:
                                                    ca_databank_cache[symbol] = ca_resp.json()
                                                except:
                                                    ca_databank_cache[symbol] = []
                                            else:
                                                ca_databank_cache[symbol] = []

                                        ca_data = ca_databank_cache.get(symbol, [])
                                        for ca in ca_data:
                                            sub = str(ca.get('subject', '')).lower()
                                            if 'dividend' in sub:
                                                match = re.search(r'(?:rs\.?|re\.?|rupees?|inr)\s*(\d+(?:\.\d+)?)', sub, re.IGNORECASE)
                                                if match:
                                                    item['EXTRACTED_DIVIDEND_AMOUNT'] = float(match.group(1))
                                                    item['EXTRACTED_DIVIDEND_TYPE'] = 'Final'
                                                    if ca.get('exDate') and ca.get('exDate') != '-':
                                                        item['EXTRACTED_RECORD_DATE'] = ca.get('exDate')
                                                    break

                                except Exception as e:
                                    logger.error(f"Failed to fetch fallback Corporate Actions for {symbol}: {e}")

                    enriched_data.append(item)"""

new_logic = r"""    def get_board_meetings(self, trade_date: date) -> pd.DataFrame:
        \"\"\"Get Board Meetings.\"\"\"
        from datetime import timedelta
        import re

        from_date_str = trade_date.strftime("%d-%m-%Y")
        to_date_str = (trade_date + timedelta(days=180)).strftime("%d-%m-%Y")
        url = f"{self.BASE_URL}/api/corporate-board-meetings?index=equities&from_date={from_date_str}&to_date={to_date_str}"

        resp = self.get(url)
        if resp is None:
            return pd.DataFrame()

        if resp.status_code == 200:
            try:
                # The JSON endpoint actually respects historical dates
                data = resp.json()
                if not data:
                     return pd.DataFrame()

                # Pre-fetch broad corporate announcements for Dividend and Record Date to avoid N+1 API calls
                global_announcements = {}
                try:
                    # We use cffi_requests if possible to bypass Akamai
                    try:
                        import curl_cffi.requests as cffi_requests
                        req_mod = cffi_requests
                        kwargs = {"impersonate": "chrome110", "timeout": 5, "headers": self.HEADERS}
                    except ImportError:
                        import requests as req_mod
                        kwargs = {"timeout": 5, "headers": self.HEADERS}

                    div_url = f"{self.BASE_URL}/api/corporate-announcements?index=equities&subject=Dividend"
                    rd_url = f"{self.BASE_URL}/api/corporate-announcements?index=equities&subject=Record%20Date"

                    for ann_url in [div_url, rd_url]:
                        ann_resp = req_mod.get(ann_url, **kwargs)
                        if ann_resp.status_code == 200:
                            for ann in ann_resp.json():
                                if not isinstance(ann, dict): continue
                                sym = ann.get('symbol')
                                if sym:
                                    if sym not in global_announcements:
                                        global_announcements[sym] = []
                                    global_announcements[sym].append(ann)
                except Exception as e:
                    logger.error(f"Failed to pre-fetch global corporate announcements: {e}")

                enriched_data = []

                for item in data:
                    item['EXTRACTED_DIVIDEND_AMOUNT'] = None
                    item['EXTRACTED_DIVIDEND_TYPE'] = None
                    item['EXTRACTED_RECORD_DATE'] = None

                    purpose = str(item.get('bm_purpose', '')).lower()
                    desc = str(item.get('bm_desc', '')).lower()

                    if 'dividend' in purpose or 'dividend' in desc:
                        symbol = item.get('bm_symbol')
                        if symbol and symbol in global_announcements:
                            found_amount = None
                            found_record_date = None
                            found_type = 'Final'

                            for ann in global_announcements[symbol]:
                                ann_desc = str(ann.get('desc', '')).lower()
                                text = str(ann.get('attchmntText', ''))

                                # Memory instruction: For dividends, use re.findall to parse and sum all matching amounts
                                if not found_amount and ('dividend' in ann_desc or 'dividend' in text.lower() or 'outcome' in ann_desc):
                                    matches = re.findall(r'(?:rs\.?|re\.?|rupees?|inr)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
                                    if matches:
                                        found_amount = sum(float(m) for m in matches)
                                        if 'interim' in text.lower(): found_type = 'Interim'
                                        elif 'special' in text.lower(): found_type = 'Special'

                                if not found_record_date and ('record date' in ann_desc or 'dividend' in ann_desc or 'record date' in text.lower()):
                                    match = re.search(r'(?:is|on)\s+(\d{1,2}[-\s][A-Za-z]{3,}[-\s]\d{2,4})', text, re.IGNORECASE)
                                    if match:
                                        found_record_date = match.group(1)

                            if found_amount:
                                item['EXTRACTED_DIVIDEND_AMOUNT'] = found_amount
                                item['EXTRACTED_DIVIDEND_TYPE'] = found_type
                            if found_record_date:
                                item['EXTRACTED_RECORD_DATE'] = found_record_date

                    enriched_data.append(item)"""

# Fix escaped quotes in new_logic to match proper docstrings
new_logic = new_logic.replace(r'\"\"\"', '"""')

if old_logic in content:
    new_content = content.replace(old_logic, new_logic)
    with open('backend/ingest/nse_lib.py', 'w') as f:
        f.write(new_content)
    print("Success")
else:
    print("Pattern not found. Let's try replacing via a unified diff or something more robust.")
