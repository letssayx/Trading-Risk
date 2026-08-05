import pandas as pd
import logging
from datetime import date, timedelta, datetime
import re
from typing import List, Dict, Any, Tuple
import requests

from backend.ingest.nse_lib import NSELib
from backend.ingest.parse_pdf import extract_amount_from_pdf

logger = logging.getLogger(__name__)

class SmartDividendImporter:
    def __init__(self):
        self.lib = NSELib()

    def fetch_board_meetings(self, start_date: date, end_date: date) -> List[Dict]:
        url = f"{self.lib.BASE_URL}/api/corporate-board-meetings?index=equities&from_date={start_date.strftime('%d-%m-%Y')}&to_date={end_date.strftime('%d-%m-%Y')}"
        resp = self.lib.get(url)
        if resp and resp.status_code == 200:
            return resp.json() if isinstance(resp.json(), list) else []
        return []

    def fetch_corporate_actions(self, start_date: date, end_date: date) -> List[Dict]:
        url = f"{self.lib.BASE_URL}/api/corporate-actions?index=equities&from_date={start_date.strftime('%d-%m-%Y')}&to_date={end_date.strftime('%d-%m-%Y')}"
        resp = self.lib.get(url)
        if resp and resp.status_code == 200:
            return resp.json() if isinstance(resp.json(), list) else []
        return []

    def fetch_announcements(self, start_date: date, end_date: date) -> List[Dict]:
        url = f"{self.lib.BASE_URL}/api/corporate-announcements?index=equities&from_date={start_date.strftime('%d-%m-%Y')}&to_date={end_date.strftime('%d-%m-%Y')}"
        resp = self.lib.get(url)
        if resp and resp.status_code == 200:
            return resp.json() if isinstance(resp.json(), list) else []
        return []

    def parse_amount_and_type(self, text: str) -> Tuple[float, str]:
        text_lower = text.lower()
        div_type = 'Dividend'
        if 'bonus' in text_lower: div_type = 'Bonus'
        elif 'split' in text_lower: div_type = 'Split'
        elif 'interim' in text_lower: div_type = 'Interim'
        elif 'final' in text_lower: div_type = 'Final'
        elif 'special' in text_lower: div_type = 'Special'

        if div_type in ['Bonus', 'Split']:
            return 0.0, div_type

        # Clean text
        _clean = re.sub(r'(?:face value|fv).*?(?:rs\.?|inr)\s*\d+(?:\.\d+)?(?:/-)?', '', text, flags=re.IGNORECASE)
        _clean = re.sub(r'\d{4}-\d{2,4}', '', _clean) # remove years

        matches = re.findall(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9|@)\s*(\d+(?:\.\d+)?)', _clean, re.IGNORECASE)
        amount = sum(float(m) for m in matches) if matches else 0.0

        # If still 0, look for %
        if amount == 0.0:
            pct_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', _clean)
            if pct_matches:
                # Need face value, but we just return None for amount to signal we need it from DB later, or we can just leave it as None
                return None, div_type

        return amount if amount > 0 else None, div_type

    def parse_dates(self, text: str) -> Tuple[str, str]:
        record_date = None
        ex_date = None

        # Try Record Date
        rd_match = re.search(r'(?:record date).*?(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]{3,9}\s+\d{4}|\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
        if rd_match:
            record_date = rd_match.group(1).replace('st','').replace('nd','').replace('rd','').replace('th','')

        # Try Ex-Date
        ex_match = re.search(r'(?:ex-date|ex date).*?(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]{3,9}\s+\d{4}|\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
        if ex_match:
            ex_date = ex_match.group(1).replace('st','').replace('nd','').replace('rd','').replace('th','')

        return record_date, ex_date

    def process(self, trade_date: date) -> pd.DataFrame:
        logger.info(f"Running Smart Dividend Importer for {trade_date}")

        # 1. Fetch Board Meetings (the anchor)
        bms = self.fetch_board_meetings(trade_date - timedelta(days=1), trade_date + timedelta(days=1))

        # 2. Fetch all Corporate Actions for a wide range (looking forward 180 days to catch Ex-Dates for Final dividends)
        cas = self.fetch_corporate_actions(trade_date - timedelta(days=10), trade_date + timedelta(days=180))

        # 3. Fetch announcements (to read XBRL text for missing dates)
        anns = self.fetch_announcements(trade_date - timedelta(days=1), trade_date + timedelta(days=2))

        results = []

        # Map CA by Symbol
        ca_by_sym = {}
        for ca in cas:
            sym = ca.get('symbol')
            if sym not in ca_by_sym: ca_by_sym[sym] = []
            ca_by_sym[sym].append(ca)

        # Map Anns by Symbol
        ann_by_sym = {}
        for ann in anns:
            sym = ann.get('symbol')
            if sym not in ann_by_sym: ann_by_sym[sym] = []
            ann_by_sym[sym].append(ann)

        processed_ca_ids = set()

        # Phase 1: Process Board Meetings (Anchors)
        for bm in bms:
            sym = bm.get('symbol')
            purpose = str(bm.get('bm_purpose', '')).lower()

            is_relevant = any(kw in purpose for kw in ['dividend', 'bonus', 'split', 'special'])
            if not is_relevant: continue

            # Broadcast date = BM Intimation Date
            bm_broadcast = bm.get('bm_timestamp', '')
            if not bm_broadcast: bm_broadcast = f"{trade_date.strftime('%Y-%m-%d')} 00:00:00"

            bm_date_str = bm.get('bm_date', '')

            amount, div_type = self.parse_amount_and_type(bm.get('bm_purpose', '') + ' ' + bm.get('bm_desc', ''))

            record_date = None
            ex_date = None

            # Look for matching Corporate Action to get exact Ex-Date (180 day window)
            matched_cas = ca_by_sym.get(sym, [])
            for ca in matched_cas:
                ca_purpose = str(ca.get('subject', '')).lower()
                ca_amount, ca_type = self.parse_amount_and_type(ca_purpose)

                # Loose matching to link them (Same type OR both are some kind of dividend, and amount matches if not None)
                types_match = (ca_type == div_type) or ('dividend' in div_type.lower() and 'dividend' in ca_type.lower())
                amounts_match = (amount is None) or (ca_amount is None) or (amount == ca_amount)

                if types_match and amounts_match:
                    if ca.get('exDate') and ca.get('exDate') != '-':
                        ex_date = ca.get('exDate')
                    if ca.get('recDate') and ca.get('recDate') != '-':
                        record_date = ca.get('recDate')

                    if ca_type != 'Dividend' and div_type == 'Dividend': div_type = ca_type
                    if ca_amount and not amount: amount = ca_amount

                    processed_ca_ids.add(f"{sym}_{ca.get('exDate')}_{ca.get('subject')}")
                    break

            # If still missing Ex-Date, scan announcements (XBRL)
            if not ex_date:
                matched_anns = ann_by_sym.get(sym, [])
                for ann in matched_anns:
                    if 'dividend' in str(ann.get('subject', '')).lower() or 'outcome' in str(ann.get('subject', '')).lower():
                        text = str(ann.get('attchmntText', '')) + " " + str(ann.get('desc', ''))
                        rd, ed = self.parse_dates(text)
                        if rd and not record_date: record_date = rd
                        if ed and not ex_date: ex_date = ed

                        ann_amt, ann_type = self.parse_amount_and_type(text)
                        if ann_amt and not amount: amount = ann_amt
                        if ann_type != 'Dividend' and div_type == 'Dividend': div_type = ann_type

            # If STILL missing Ex-Date/Amount, deep scan PDF (Coal India case)
            if (not ex_date or not amount or div_type == 'Dividend'):
                attachment_url = str(bm.get('ATTACHMENT', ''))
                if not attachment_url and ann_by_sym.get(sym):
                    attachment_url = str(ann_by_sym.get(sym)[0].get('attchmntFile', ''))

                if attachment_url.startswith('http'):
                    pdf_amt, pdf_rd, pdf_type, _ = extract_amount_from_pdf(attachment_url)
                    if pdf_amt and not amount: amount = pdf_amt
                    if pdf_rd and not record_date:
                        record_date = pdf_rd
                        ex_date = pdf_rd # Default Indian Market T+1
                    if pdf_type and div_type == 'Dividend': div_type = pdf_type

            # Fallback Record Date to Ex-Date
            if record_date and not ex_date:
                ex_date = record_date

            results.append({
                'SYMBOL': sym,
                'COMPANY NAME': bm.get('sm_name', ''),
                'PURPOSE': bm.get('bm_purpose', ''),
                'BM_DESC': bm.get('bm_desc', ''),
                'MEETING DATE': bm_date_str,
                'BROADCAST DATE': bm_broadcast,
                'ATTACHMENT': bm.get('ATTACHMENT', ''),
                'EXTRACTED_DIVIDEND_AMOUNT': amount,
                'EXTRACTED_DIVIDEND_TYPE': div_type,
                'EXTRACTED_RECORD_DATE': record_date,
                'EX-DATE': ex_date,
                'IS_AGM': False
            })

        # Phase 2: Add orphaned Corporate Actions (actions that had no BM in this date window)
        for ca in cas:
            sym = ca.get('symbol')
            ca_id = f"{sym}_{ca.get('exDate')}_{ca.get('subject')}"

            if ca_id in processed_ca_ids: continue

            subject = str(ca.get('subject', '')).lower()
            is_relevant = any(kw in subject for kw in ['dividend', 'bonus', 'split', 'special'])
            if not is_relevant: continue

            amount, div_type = self.parse_amount_and_type(ca.get('subject', ''))

            ex_date = ca.get('exDate')
            if ex_date == '-': ex_date = ca.get('recDate') if ca.get('recDate') != '-' else None

            results.append({
                'SYMBOL': sym,
                'COMPANY NAME': ca.get('comp', ''),
                'PURPOSE': ca.get('subject', ''),
                'BM_DESC': '',
                'MEETING DATE': None,  # CA doesn't have BM date natively
                'BROADCAST DATE': ca.get('caBroadcastDate', f"{trade_date.strftime('%Y-%m-%d')} 00:00:00"),
                'ATTACHMENT': '',
                'EXTRACTED_DIVIDEND_AMOUNT': amount,
                'EXTRACTED_DIVIDEND_TYPE': div_type,
                'EXTRACTED_RECORD_DATE': ca.get('recDate', None) if ca.get('recDate') != '-' else None,
                'EX-DATE': ex_date,
                'IS_AGM': False
            })

        df = pd.DataFrame(results)
        if not df.empty:
            # Format dates nicely
            df['BROADCAST DATE'] = pd.to_datetime(df['BROADCAST DATE'], errors='coerce')
            df['MEETING DATE'] = pd.to_datetime(df['MEETING DATE'], errors='coerce')

            # Deduplication: To fix DLF duplicate, we prioritize the row that has a valid EX-DATE
            df['_has_ex_date'] = df['EX-DATE'].notna() & (df['EX-DATE'] != '')

            # Sort so rows with EX-DATE come last (keep='last' will keep them)
            df = df.sort_values(['_has_ex_date', 'BROADCAST DATE'])

            # Deduplicate strictly on Symbol, Meeting Date (if exists) or Ex-Date, and Type
            # Split to handle safely
            df_bm = df[df['MEETING DATE'].notna()]
            df_ca = df[df['MEETING DATE'].isna()]

            if not df_bm.empty:
                df_bm = df_bm.drop_duplicates(subset=['SYMBOL', 'MEETING DATE', 'EXTRACTED_DIVIDEND_TYPE'], keep='last')

            if not df_ca.empty:
                df_ca = df_ca.drop_duplicates(subset=['SYMBOL', 'EX-DATE', 'EXTRACTED_DIVIDEND_TYPE'], keep='last')

            df = pd.concat([df_bm, df_ca], ignore_index=True)

            df['BROADCAST DATE'] = df['BROADCAST DATE'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df['MEETING DATE'] = df['MEETING DATE'].dt.strftime('%Y-%m-%d')
            df = df.drop(columns=['_has_ex_date', 'IS_AGM'])

        return df

    def process_agms(self, trade_date: date) -> pd.DataFrame:
        logger.info(f"Running Smart AGM Importer for {trade_date}")

        anns = self.fetch_announcements(trade_date - timedelta(days=7), trade_date + timedelta(days=180))

        results = []
        for ann in anns:
            subj = str(ann.get('subject', '')).lower()
            desc = str(ann.get('desc', '')).lower()
            text = str(ann.get('attchmntText', '')).lower()

            is_agm = 'agm' in subj or 'annual general meeting' in subj or 'agm' in desc or 'annual general meeting' in desc
            if not is_agm: continue

            agm_date = None
            if 'dateofannualgeneralmeeting' in text:
                agm_date_match = re.search(r'<[^>]*DateOfAnnualGeneralMeeting[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{4}-\d{2}-\d{2}).*?</[^>]*>', text, re.IGNORECASE)
                if agm_date_match: agm_date = agm_date_match.group(1)

            if not agm_date:
                fallback_agm = re.search(r'(?:agm|annual general meeting).*?(?:on|dated|scheduled for|-)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]{3,9}\s+\d{4}|\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', text + " " + subj + " " + desc, re.IGNORECASE)
                if fallback_agm:
                    agm_date = fallback_agm.group(1).replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')

            if agm_date:
                try:
                    ann_date = datetime.strptime(ann.get('an_dt', '').split(' ')[0], "%d-%b-%Y").strftime('%Y-%m-%d')
                except Exception:
                    ann_date = trade_date.strftime('%Y-%m-%d')

                results.append({
                    'SYMBOL': ann.get('symbol', ''),
                    'COMPANY NAME': ann.get('sm_name', ''),
                    'PURPOSE': ann.get('subject', ''),
                    'MEETING DATE': None,
                    'BROADCAST DATE': ann_date,
                    'EXTRACTED_DIVIDEND_AMOUNT': None,
                    'EXTRACTED_DIVIDEND_TYPE': 'AGM',
                    'EXTRACTED_RECORD_DATE': None,
                    'EX-DATE': agm_date
                })

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.drop_duplicates(subset=['SYMBOL', 'BROADCAST DATE', 'EX-DATE', 'EXTRACTED_DIVIDEND_TYPE'])

        return df
