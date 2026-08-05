"""Standalone foolproof importer for Dividends and AGMs."""

import pandas as pd
import logging
import re
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional

from backend.ingest.nse_lib import NSELib
from backend.ingest.parse_pdf import extract_amount_from_pdf

logger = logging.getLogger(__name__)

def fetch_and_parse_dividends(trade_date: date) -> pd.DataFrame:
    """
    Fetches corporate board meetings and actions, merges them cleanly without mixing up old dates,
    and returns a robust DataFrame matching the DividendDatabank structure.
    """
    lib = NSELib()

    # 1. Strict daily fetch window matching the legacy setup (or up to 180 days forward for Ex-Dates)
    from_date_str = (trade_date - timedelta(days=7)).strftime("%d-%m-%Y")
    to_date_str = (trade_date + timedelta(days=180)).strftime("%d-%m-%Y")

    logger.info(f"Fetching standalone dividends for trade_date={trade_date}")

    # Fetch endpoints
    bm_url = f"{lib.BASE_URL}/api/corporate-board-meetings?index=equities&from_date={from_date_str}&to_date={to_date_str}"
    ca_url = f"{lib.BASE_URL}/api/corporates-corporateActions?index=equities&from_date={from_date_str}&to_date={to_date_str}"

    bm_resp = lib.get(bm_url)
    ca_resp = lib.get(ca_url)

    bms = bm_resp.json() if bm_resp and bm_resp.status_code == 200 and isinstance(bm_resp.json(), list) else []
    cas = ca_resp.json() if ca_resp and ca_resp.status_code == 200 and isinstance(ca_resp.json(), list) else []

    # Map CAs by symbol for easy lookup
    ca_map = {}
    for ca in cas:
        sym = ca.get('symbol')
        if sym:
            ca_map.setdefault(sym, []).append(ca)

    # 2. Extract specific announcements to extract XBRL attachment texts
    announcement_urls = [
        f"{lib.BASE_URL}/api/corporate-announcements?index=equities&subject=Dividend",
        f"{lib.BASE_URL}/api/corporate-announcements?index=equities&subject=Record%20Date",
        f"{lib.BASE_URL}/api/corporate-announcements?index=equities&from_date={from_date_str}&to_date={to_date_str}"
    ]

    announcements = []
    for url in announcement_urls:
        resp = lib.get(url)
        if resp and resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                announcements.extend(data)

    ann_map = {}
    for ann in announcements:
        sym = ann.get('symbol')
        if sym:
            ann_map.setdefault(sym, []).append(ann)

    results = []

    # Process Board Meetings
    for bm in bms:
        symbol = bm.get('bm_symbol')
        if not symbol:
            continue

        purpose = str(bm.get('bm_purpose', '')).lower()
        desc = str(bm.get('bm_desc', '')).lower()

        # Check if this BM is about dividends, splits, or bonuses
        has_div = 'dividend' in purpose or 'dividend' in desc or 'intdiv' in purpose or 'findiv' in purpose
        has_split = 'split' in purpose or 'sub-division' in purpose
        has_bonus = 'bonus' in purpose

        if not (has_div or has_split or has_bonus):
            continue

        try:
            bm_date = datetime.strptime(bm.get('bm_date', ''), "%d-%b-%Y").date()
        except Exception:
            continue

        if bm_date > trade_date:
            continue # Don't parse future meetings yet

        bm_timestamp = bm.get('bm_timestamp')

        # Find matching CAs
        matched_cas = []
        for ca in ca_map.get(symbol, []):
            try:
                ca_ex_date = datetime.strptime(str(ca.get('exDate', '')), "%d-%b-%Y").date()
                if ca_ex_date >= bm_date: # Ex-date must be after or on BM date
                    matched_cas.append(ca)
            except Exception:
                pass

        # Find matching announcements
        matched_anns = []
        for ann in ann_map.get(symbol, []):
            try:
                ann_date = datetime.strptime(ann.get('an_dt', '').split(' ')[0], "%d-%b-%Y").date()
                if 0 <= (ann_date - bm_date).days <= 3:
                    matched_anns.append(ann)
            except Exception:
                pass

        # We will parse amounts, dates, and types strictly
        def extract_info(text_to_search: str, is_ca: bool = False):
            info = {'amount': None, 'type': None, 'record_date': None, 'ex_date': None}
            text_to_search = text_to_search.lower()

            # Type
            if has_bonus or 'bonus' in text_to_search: info['type'] = 'Bonus'
            elif has_split or 'split' in text_to_search: info['type'] = 'Split'
            elif 'interim' in text_to_search or 'intdiv' in text_to_search: info['type'] = 'Interim'
            elif 'final' in text_to_search or 'findiv' in text_to_search: info['type'] = 'Final'
            elif 'special' in text_to_search: info['type'] = 'Special'
            elif has_div: info['type'] = 'Dividend'

            # Amount
            _clean = re.sub(r'(?:face value|fv|paid-up capital|equity shares?).*?(?:rs\.?|inr)\s*\d+(?:\.\d+)?(?:/-)?', '', text_to_search, flags=re.IGNORECASE)
            matches = re.findall(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean, re.IGNORECASE)
            if matches:
                info['amount'] = sum(float(m) for m in matches)
            else:
                xbrl = re.findall(r'<[^>]*Dividend[^>]*>.*?Rs\.?\s*(\d+(?:\.\d+)?).*?</[^>]*>', text_to_search, re.IGNORECASE)
                if xbrl:
                    info['amount'] = sum(float(m) for m in xbrl)

            # Record/Ex Date
            rd_match = re.search(r'<[^>]*RecordDate[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}).*?</[^>]*>', text_to_search, re.IGNORECASE)
            if rd_match:
                info['record_date'] = rd_match.group(1)
            else:
                ex_match = re.search(r'(?:ex-date|ex date|record date).*?(\d{1,2}-[a-zA-Z]{3}-\d{4})', text_to_search, re.IGNORECASE)
                if ex_match:
                    info['record_date'] = ex_match.group(1)
                    info['ex_date'] = ex_match.group(1)

            return info

        best_info = extract_info(purpose + " " + desc)

        # Enhance with CA data
        for ca in matched_cas:
            ca_info = extract_info(str(ca.get('subject', '')))
            if ca_info['amount'] and not best_info['amount']: best_info['amount'] = ca_info['amount']
            if ca_info['type'] and best_info['type'] == 'Dividend': best_info['type'] = ca_info['type']
            if ca.get('exDate') and ca.get('exDate') != '-': best_info['ex_date'] = ca.get('exDate')
            if ca.get('recDate') and ca.get('recDate') != '-': best_info['record_date'] = ca.get('recDate')

        # Enhance with Announcements (XBRL)
        for ann in matched_anns:
            ann_info = extract_info(str(ann.get('attchmntText', '')) + " " + str(ann.get('subject', '')) + " " + str(ann.get('desc', '')))
            if ann_info['amount'] and not best_info['amount']: best_info['amount'] = ann_info['amount']
            if ann_info['type'] and best_info['type'] == 'Dividend': best_info['type'] = ann_info['type']
            if ann_info['record_date'] and not best_info['record_date']: best_info['record_date'] = ann_info['record_date']
            if ann_info['ex_date'] and not best_info['ex_date']: best_info['ex_date'] = ann_info['ex_date']

        # Fallback to PDF Scraping specifically for missing Data (Coal India Fix)
        if not best_info['ex_date'] or not best_info['amount'] or best_info['type'] == 'Dividend':
            attachment_url = str(bm.get('ATTACHMENT', ''))
            if not attachment_url and matched_anns:
                attachment_url = str(matched_anns[0].get('attchmntFile', ''))

            if attachment_url.startswith('http'):
                pdf_amt, pdf_rd, pdf_type, _ = extract_amount_from_pdf(attachment_url)
                if pdf_amt and not best_info['amount']: best_info['amount'] = pdf_amt
                if pdf_rd and not best_info['record_date']:
                    best_info['record_date'] = pdf_rd
                    best_info['ex_date'] = pdf_rd # Indian market T+1
                if pdf_type and best_info['type'] == 'Dividend': best_info['type'] = pdf_type

        # Ensure Ex-date fallback if missing
        if best_info['record_date'] and not best_info['ex_date']:
            best_info['ex_date'] = best_info['record_date']

        results.append({
            'SYMBOL': symbol,
            'COMPANY NAME': bm.get('sm_name', ''),
            'PURPOSE': bm.get('bm_purpose', ''),
            'BM_DESC': bm.get('bm_desc', ''),
            'MEETING DATE': bm.get('bm_date', ''),
            'BROADCAST DATE': bm_timestamp,
            'ATTACHMENT': bm.get('ATTACHMENT', ''),
            'EXTRACTED_DIVIDEND_AMOUNT': best_info['amount'],
            'EXTRACTED_DIVIDEND_TYPE': best_info['type'],
            'EXTRACTED_RECORD_DATE': best_info['record_date'],
            'EX-DATE': best_info['ex_date'],
        })

    # Add standalone Corporate Actions (that had no matching BM)
    consumed_cas = set()
    for row in results:
        sym = row['SYMBOL']
        row_ex = row.get('EX-DATE')
        row_rd = row.get('EXTRACTED_RECORD_DATE')
        if row_ex or row_rd:
            for c in ca_map.get(sym, []):
                c_ex = c.get('exDate')
                c_rd = c.get('recDate')
                if (row_ex and c_ex == row_ex) or (row_rd and c_rd == row_rd):
                    consumed_cas.add(f"{sym}_{c_ex}_{c.get('subject')}")

    for ca in cas:
        sym = ca.get('symbol')
        ex_date = ca.get('exDate')
        subject = ca.get('subject')

        ca_key = f"{sym}_{ex_date}_{subject}"
        if ca_key in consumed_cas:
            continue

        has_div = 'dividend' in str(subject).lower()
        has_split = 'split' in str(subject).lower()
        has_bonus = 'bonus' in str(subject).lower()

        if not (has_div or has_split or has_bonus):
            continue

        info = {'amount': None, 'type': 'Dividend'}
        if has_bonus: info['type'] = 'Bonus'
        elif has_split: info['type'] = 'Split'
        elif 'interim' in str(subject).lower(): info['type'] = 'Interim'
        elif 'final' in str(subject).lower(): info['type'] = 'Final'
        elif 'special' in str(subject).lower(): info['type'] = 'Special'

        _clean = re.sub(r'(?:face value|fv).*?(?:rs\.?|inr)\s*\d+(?:\.\d+)?(?:/-)?', '', str(subject), flags=re.IGNORECASE)
        matches = re.findall(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean, re.IGNORECASE)
        if matches:
            info['amount'] = sum(float(m) for m in matches)

        results.append({
            'SYMBOL': sym,
            'COMPANY NAME': ca.get('comp', ''),
            'PURPOSE': subject,
            'BM_DESC': '',
            'MEETING DATE': None,
            'BROADCAST DATE': ca.get('caBroadcastDate', ''),
            'ATTACHMENT': '',
            'EXTRACTED_DIVIDEND_AMOUNT': info['amount'],
            'EXTRACTED_DIVIDEND_TYPE': info['type'],
            'EXTRACTED_RECORD_DATE': ca.get('recDate', ''),
            'EX-DATE': ex_date if ex_date and ex_date != '-' else ca.get('recDate', ''),
        })

    # Deduplicate strictly (Symbol, Ex-Date, Type) to fix DLF Duplicates
    df = pd.DataFrame(results)
    if not df.empty:
        # Sort by Broadcast Date and prioritize rows that actually HAVE an EX-DATE
        df['BROADCAST DATE'] = pd.to_datetime(df['BROADCAST DATE'], errors='coerce')
        df['_has_ex_date'] = df['EX-DATE'].astype(bool)

        # Sort so that rows with Ex-Date are kept over rows without Ex-Date
        df = df.sort_values(['_has_ex_date', 'BROADCAST DATE'])

        df['MEETING DATE'] = pd.to_datetime(df['MEETING DATE'], errors='coerce')

        # DLF Duplicate Fix: If Symbol, Meeting Date, and Dividend Type match, it's the exact same dividend.
        # We can drop duplicates keeping the last one (which, due to our sort, will have the EX-DATE if one exists).
        # Important: Don't drop valid distinct standalone CAs where Meeting Date is NaT.

        # Split into rows with Meeting Date and standalone CAs (without Meeting Date)
        df_bm = df[df['MEETING DATE'].notna()]
        df_ca = df[df['MEETING DATE'].isna()]

        if not df_bm.empty:
            df_bm = df_bm.drop_duplicates(subset=['SYMBOL', 'MEETING DATE', 'EXTRACTED_DIVIDEND_TYPE'], keep='last')

        if not df_ca.empty:
            df_ca = df_ca.drop_duplicates(subset=['SYMBOL', 'EX-DATE', 'EXTRACTED_DIVIDEND_TYPE'], keep='last')

        df = pd.concat([df_bm, df_ca], ignore_index=True)

        df['BROADCAST DATE'] = df['BROADCAST DATE'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['MEETING DATE'] = df['MEETING DATE'].dt.strftime('%d-%b-%Y')
        df = df.drop(columns=['_has_ex_date'])

    return df

def fetch_and_parse_agms(trade_date: date) -> pd.DataFrame:
    """
    Fetches strictly AGM events to populate the AGMEvent table separately.
    """
    lib = NSELib()
    from_date_str = (trade_date - timedelta(days=7)).strftime("%d-%m-%Y")
    to_date_str = (trade_date + timedelta(days=180)).strftime("%d-%m-%Y")

    logger.info(f"Fetching standalone AGMs for trade_date={trade_date}")

    url = f"{lib.BASE_URL}/api/corporate-announcements?index=equities&from_date={from_date_str}&to_date={to_date_str}"
    resp = lib.get(url)

    agms = []
    if resp and resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list):
            for ann in data:
                subj = str(ann.get('subject', '')).lower()
                desc = str(ann.get('desc', '')).lower()
                text = str(ann.get('attchmntText', '')).lower()

                is_agm = 'agm' in subj or 'annual general meeting' in subj or 'agm' in desc or 'annual general meeting' in desc
                if not is_agm:
                    continue

                agm_date = None
                if 'dateofannualgeneralmeeting' in text:
                    agm_date_match = re.search(r'<[^>]*DateOfAnnualGeneralMeeting[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{4}-\d{2}-\d{2}).*?</[^>]*>', text, re.IGNORECASE)
                    if agm_date_match:
                        agm_date = agm_date_match.group(1)

                if not agm_date:
                    fallback_agm = re.search(r'(?:agm|annual general meeting).*?(?:on|dated|scheduled for|-)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]{3,9}\s+\d{4}|\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', text + " " + subj + " " + desc, re.IGNORECASE)
                    if fallback_agm:
                        agm_date = fallback_agm.group(1).replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')

                if agm_date:
                    try:
                        ann_date = datetime.strptime(ann.get('an_dt', '').split(' ')[0], "%d-%b-%Y").strftime('%Y-%m-%d')
                    except Exception:
                        ann_date = trade_date.strftime('%Y-%m-%d')

                    agms.append({
                        'SYMBOL': ann.get('symbol', ''),
                        'COMPANY NAME': ann.get('sm_name', ''),
                        'AGM_ANNOUNCEMENT_DATE': ann_date,
                        'AGM_DATE': agm_date
                    })

    df = pd.DataFrame(agms)
    if not df.empty:
        df = df.drop_duplicates(subset=['SYMBOL', 'AGM_ANNOUNCEMENT_DATE', 'AGM_DATE'])
    return df
