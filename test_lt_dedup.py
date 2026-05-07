from datetime import datetime, date
import curl_cffi.requests as req_mod
import pandas as pd
import re
import sys
sys.path.append('.')
from backend.ingest.nse_lib import NSELib

lib = NSELib()

def test_fetch():
    # Use the target board meeting date
    bm_date = date(2026, 5, 5) # From user screenshot, LT has board meeting on 2026-05-05
    from_date_str = "01-05-2026"
    to_date_str = "10-05-2026"

    url = f"{lib.BASE_URL}/api/corporate-board-meetings?index=equities&from_date={from_date_str}&to_date={to_date_str}"
    print(f"Fetching board meetings for {from_date_str} to {to_date_str}...")
    resp = req_mod.get(url, headers=lib.HEADERS, impersonate="chrome110")
    if resp.status_code != 200:
        print("Failed to fetch BM")
        return
    data = resp.json()

    # Filter for LT
    lt_bms = [item for item in data if item.get('bm_symbol') == 'LT']
    print(f"Found {len(lt_bms)} BM records for LT.")
    for bm in lt_bms:
        print("BM PURPOSE:", bm.get('bm_purpose'), "DESC:", bm.get('bm_desc'))

    print("Pre-fetching corporate announcements for LT...")
    ann_url = f"{lib.BASE_URL}/api/corporate-announcements?index=equities&symbol=LT"
    ann_resp = req_mod.get(ann_url, headers=lib.HEADERS, impersonate="chrome110")

    lt_anns = ann_resp.json()
    print(f"Fetched {len(lt_anns)} announcements for LT")

    enriched_data = []
    global_announcements = {'LT': lt_anns}

    for item in lt_bms:
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

                try:
                    bm_date_obj = datetime.strptime(item.get('bm_date', ''), "%d-%b-%Y").date()
                except ValueError:
                    bm_date_obj = None

                print(f"Checking announcements for BM Date: {bm_date_obj}")

                for ann in global_announcements[symbol]:
                    if bm_date_obj:
                        an_dt_str = ann.get('an_dt', '')
                        try:
                            an_dt_obj = datetime.strptime(an_dt_str[:11], "%d-%b-%Y").date()
                            days_diff = (an_dt_obj - bm_date_obj).days
                            if days_diff < -1 or days_diff > 10:
                                continue  # Skip stale announcements
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
                            print(f" -> Found Amount {found_amount} in {ann_desc}")

                    if not found_record_date and ('record date' in ann_desc or 'dividend' in ann_desc or 'record date' in text.lower()):
                        match = re.search(r'(?:is|on)\s+(\d{1,2}[-\s][A-Za-z]{3,}[-\s]\d{2,4})', text, re.IGNORECASE)
                        if match:
                            found_record_date = match.group(1)
                            print(f" -> Found Record Date {found_record_date} in {ann_desc}")

                if found_amount:
                    item['EXTRACTED_DIVIDEND_AMOUNT'] = found_amount
                    item['EXTRACTED_DIVIDEND_TYPE'] = found_type
                if found_record_date:
                    item['EXTRACTED_RECORD_DATE'] = found_record_date

        enriched_data.append(item)

    df = pd.DataFrame(enriched_data)
    print(df[['bm_symbol', 'bm_purpose', 'EXTRACTED_DIVIDEND_AMOUNT', 'EXTRACTED_RECORD_DATE']])

test_fetch()
