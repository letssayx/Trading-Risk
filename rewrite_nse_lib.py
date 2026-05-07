import re

with open('backend/ingest/nse_lib.py', 'r') as f:
    content = f.read()

# Replace the get_board_meetings function
new_func = """    def get_board_meetings(self, trade_date: date) -> pd.DataFrame:
        \"\"\"Get Board Meetings.\"\"\"
        from datetime import timedelta, datetime
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

                # Filter down to just elements that have "dividend"
                dividend_items = []
                for item in data:
                    purpose = str(item.get('bm_purpose', '')).lower()
                    desc = str(item.get('bm_desc', '')).lower()
                    if 'dividend' in purpose or 'dividend' in desc:
                        dividend_items.append(item)

                # Fetch specific symbol announcements for just these to be fast, bypassing N+1 full loops if possible
                try:
                    try:
                        import curl_cffi.requests as cffi_requests
                        req_mod = cffi_requests
                        kwargs = {"impersonate": "chrome110", "timeout": 5, "headers": self.HEADERS}
                    except ImportError:
                        import requests as req_mod
                        kwargs = {"timeout": 5, "headers": self.HEADERS}
                except Exception:
                    pass

                # Cache of symbol -> announcements
                symbol_announcements = {}
                enriched_data = []

                for item in data:
                    item['EXTRACTED_DIVIDEND_AMOUNT'] = None
                    item['EXTRACTED_DIVIDEND_TYPE'] = None
                    item['EXTRACTED_RECORD_DATE'] = None

                    purpose = str(item.get('bm_purpose', '')).lower()
                    desc = str(item.get('bm_desc', '')).lower()

                    if 'dividend' in purpose or 'dividend' in desc:
                        symbol = item.get('bm_symbol')

                        if symbol and symbol not in symbol_announcements:
                            try:
                                ann_url = f"{self.BASE_URL}/api/corporate-announcements?index=equities&symbol={symbol}"
                                ann_resp = req_mod.get(ann_url, **kwargs)
                                if ann_resp.status_code == 200:
                                    symbol_announcements[symbol] = ann_resp.json()
                                else:
                                    symbol_announcements[symbol] = []
                            except Exception as e:
                                logger.error(f"Failed to fetch announcements for {symbol}: {e}")
                                symbol_announcements[symbol] = []

                        if symbol and symbol in symbol_announcements:
                            found_amount = None
                            found_record_date = None
                            found_type = 'Final'

                            try:
                                bm_date_obj = datetime.strptime(item.get('bm_date', ''), "%d-%b-%Y").date()
                            except ValueError:
                                bm_date_obj = None

                            for ann in symbol_announcements[symbol]:
                                if not isinstance(ann, dict): continue

                                if bm_date_obj:
                                    an_dt_str = ann.get('an_dt', '')
                                    try:
                                        an_dt_obj = datetime.strptime(an_dt_str[:11], "%d-%b-%Y").date()
                                        days_diff = (an_dt_obj - bm_date_obj).days
                                        if days_diff < -1 or days_diff > 10:
                                            continue
                                    except ValueError:
                                        pass

                                ann_desc = str(ann.get('desc', '')).lower()
                                text = str(ann.get('attchmntText', ''))

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

                    enriched_data.append(item)

                df = pd.DataFrame(enriched_data)
                mapping = {
                    'bm_symbol': 'SYMBOL',
                    'sm_name': 'COMPANY NAME',
                    'bm_purpose': 'PURPOSE',
                    'bm_desc': 'BM_DESC',
                    'bm_date': 'MEETING DATE',
                    'bm_timestamp': 'BROADCAST DATE',
                    'ATTACHMENT': 'ATTACHMENT'
                }
                df = df.rename(columns=mapping)
                return df
            except Exception as e:
                logger.error(f"Board Meetings parse error: {e}")
        return pd.DataFrame()"""

# Replace in content
import re
new_content = re.sub(r'    def get_board_meetings\(self, trade_date: date\) -> pd\.DataFrame:.*?        return pd\.DataFrame\(\)', new_func, content, flags=re.DOTALL)

with open('backend/ingest/nse_lib.py', 'w') as f:
    f.write(new_content)
