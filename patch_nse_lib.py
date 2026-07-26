import re

with open('backend/ingest/nse_lib.py', 'r') as f:
    content = f.read()

replacement = r"""
                enriched_data = []
                consumed_announcements = set()

                for item in data:
                    item['EXTRACTED_DIVIDEND_AMOUNT'] = None
                    item['EXTRACTED_DIVIDEND_TYPE'] = None
                    item['EXTRACTED_RECORD_DATE'] = None

                    purpose = str(item.get('bm_purpose', '')).lower()
                    desc = str(item.get('bm_desc', '')).lower()
                    symbol = item.get('bm_symbol')

                    has_dividend_mention = 'dividend' in purpose or 'dividend' in desc or 'intdiv' in purpose or 'int div' in purpose or 'intdiv' in desc or 'int div' in desc or 'findiv' in purpose or 'fin div' in purpose or 'findiv' in desc or 'fin div' in desc

                    try:
                        bm_date_obj_check = datetime.strptime(item.get('bm_date', ''), "%d-%b-%Y").date()
                    except ValueError:
                        bm_date_obj_check = None

                    is_agm = 'annual general meeting' in purpose or 'agm' in purpose

                    matched_anns = []
                    if symbol and symbol in symbol_announcements and bm_date_obj_check:
                        for ann in symbol_announcements[symbol]:
                            subj = str(ann.get('subject', '')).lower()
                            if 'dividend' in subj or 'record date' in subj:
                                ann_date_str = ann.get('an_dt', '')
                                try:
                                    ann_date_obj = datetime.strptime(ann_date_str.split(' ')[0], "%d-%b-%Y").date()
                                    if 0 <= (ann_date_obj - bm_date_obj_check).days <= 3:
                                        has_dividend_mention = True
                                        matched_anns.append(ann)
                                        consumed_announcements.add(ann.get('seq_id'))
                                except ValueError:
                                    pass
                            elif 'shareholders meeting' in subj or 'agm' in subj or 'annual general meeting' in subj:
                                ann_date_str = ann.get('an_dt', '')
                                try:
                                    ann_date_obj = datetime.strptime(ann_date_str.split(' ')[0], "%d-%b-%Y").date()
                                    if 0 <= (ann_date_obj - bm_date_obj_check).days <= 3:
                                        is_agm = True
                                        matched_anns.append(ann)
                                        consumed_announcements.add(ann.get('seq_id'))
                                except ValueError:
                                    pass

                    if has_dividend_mention or is_agm:
                        # For RECLTD, if we found multiple announcements for the same board meeting day
                        # (e.g. Interim and Final), we should create a separate item for each announcement
                        # However, to maintain backwards compatibility, we'll try standard parsing first.
                        # If there are multiple distinct record dates in the matched announcements, we'll branch them out.

                        base_type = 'Final' if ('final' in purpose or 'findiv' in purpose or 'fin div' in purpose) else ('Interim' if 'interim' in purpose or 'intdiv' in purpose or 'int div' in purpose else ('Special' if 'special' in purpose else 'Final'))
                        if is_agm:
                            base_type = 'AGM'
                            item['bm_purpose'] = 'Annual General Meeting'

                        # If we have matched announcements, let's process each one separately if it yields distinct data
                        if matched_anns:
                            for ann in matched_anns:
                                new_item = item.copy()
                                found_amount = None
                                found_record_date = None
                                found_type = base_type

                                attchmntText = ann.get('attchmntText', '')

                                # Extract Amount
                                xbrl_matches = re.findall(r'<[^>]*Dividend[^>]*>.*?Rs\.?\s*(\d+(?:\.\d+)?).*?</[^>]*>', attchmntText, re.IGNORECASE)
                                if not xbrl_matches:
                                    xbrl_matches = re.findall(r'<[^>]*Dividend[^>]*>.*?(\d+(?:\.\d+)?).*?</[^>]*>', attchmntText, re.IGNORECASE)
                                if xbrl_matches:
                                    found_amount = sum(float(m) for m in xbrl_matches)

                                if 'DateOfAnnualGeneralMeeting' in attchmntText:
                                    agm_date_match = re.search(r'<[^>]*DateOfAnnualGeneralMeeting[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}).*?</[^>]*>', attchmntText, re.IGNORECASE)
                                    if agm_date_match:
                                        new_item['bm_purpose'] = str(new_item.get('bm_purpose') or '') + f" - AGM - {agm_date_match.group(1)}"

                                if found_amount is None:
                                    _clean_text = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9)*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', attchmntText, flags=re.IGNORECASE)

                                    if 'including' in _clean_text.lower() or 'includes' in _clean_text.lower():
                                        match = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_text, re.IGNORECASE)
                                        if match:
                                            found_amount = float(match.group(1))
                                    else:
                                        div_pattern = re.compile(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', re.IGNORECASE)
                                        matches = div_pattern.findall(_clean_text)
                                        if matches:
                                            found_amount = sum(float(m) for m in matches)

                                # Also check for specific types in the announcement text itself
                                text_lower = attchmntText.lower()
                                if 'interim' in text_lower or 'intdiv' in text_lower: found_type = 'Interim'
                                elif 'final' in text_lower or 'findiv' in text_lower: found_type = 'Final'
                                elif 'special' in text_lower: found_type = 'Special'

                                # Extract Record Date
                                date_pattern = re.compile(r'(\d{1,2}-[a-zA-Z]{3}-\d{4})')
                                record_date_match = re.search(r'<[^>]*RecordDate[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}).*?</[^>]*>', attchmntText, re.IGNORECASE)
                                if record_date_match:
                                    found_record_date = record_date_match.group(1)

                                if not found_record_date:
                                    ex_date_match = re.search(r'(?:ex-date|ex date).*?(\d{1,2}-[a-zA-Z]{3}-\d{4})', attchmntText, re.IGNORECASE)
                                    if ex_date_match:
                                        found_record_date = ex_date_match.group(1)

                                if not found_record_date:
                                    date_match = date_pattern.search(attchmntText)
                                    if date_match and 'record date' in attchmntText.lower():
                                        found_record_date = date_match.group(1)

                                if found_amount:
                                    new_item['EXTRACTED_DIVIDEND_AMOUNT'] = found_amount
                                    new_item['EXTRACTED_DIVIDEND_TYPE'] = found_type
                                if found_record_date:
                                    new_item['EXTRACTED_RECORD_DATE'] = found_record_date

                                # Prevent exact duplicates from multiple announcements
                                is_dup = False
                                for e in enriched_data:
                                    if e.get('bm_symbol') == new_item['bm_symbol'] and e.get('EXTRACTED_RECORD_DATE') == new_item['EXTRACTED_RECORD_DATE'] and e.get('EXTRACTED_DIVIDEND_TYPE') == new_item['EXTRACTED_DIVIDEND_TYPE']:
                                        is_dup = True
                                        break
                                if not is_dup:
                                    enriched_data.append(new_item)
                            continue # skip adding the base item since we added the matched branches

                        # Base fallback if no matched announcements or we just want to fall back to CA mapping
                        found_amount = None
                        found_record_date = None
                        found_type = base_type

                        if symbol and symbol in symbol_ca_map:
                            try:
                                bm_date_obj = datetime.strptime(item.get('bm_date', ''), "%d-%b-%Y").date()
                            except ValueError:
                                bm_date_obj = None

                            for ca in symbol_ca_map[symbol]:
                                ca_ex_date_str = str(ca.get('exDate', ''))
                                try:
                                    ca_ex_date_obj = datetime.strptime(ca_ex_date_str, "%d-%b-%Y").date()
                                except ValueError:
                                    ca_ex_date_obj = None

                                if bm_date_obj and ca_ex_date_obj:
                                    days_diff = (ca_ex_date_obj - bm_date_obj).days
                                    if days_diff < -1:
                                        continue

                                subject = str(ca.get('subject', ''))

                                _clean_subject = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9)*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', subject, flags=re.IGNORECASE)
                                if 'including' in _clean_subject.lower() or 'includes' in _clean_subject.lower():
                                    match = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_subject, re.IGNORECASE)
                                    if match:
                                        found_amount = float(match.group(1))
                                else:
                                    matches = re.findall(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_subject, re.IGNORECASE)
                                    if matches:
                                        found_amount = sum(float(m) for m in matches)

                                if found_amount:
                                    if 'interim' in subject.lower() or 'intdiv' in subject.lower() or 'int div' in subject.lower(): found_type = 'Interim'
                                    elif 'findiv' in subject.lower() or 'fin div' in subject.lower() or 'final' in subject.lower(): found_type = 'Final'
                                    elif 'special' in subject.lower(): found_type = 'Special'

                                rec_date = ca.get('recDate')
                                if rec_date and rec_date != '-':
                                    found_record_date = rec_date

                                if found_amount or found_record_date:
                                    break

                        if found_amount is None:
                            text_to_search = f"{purpose} {desc}"
                            _clean_text_2 = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9)*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', text_to_search, flags=re.IGNORECASE)

                            if 'including' in _clean_text_2.lower() or 'includes' in _clean_text_2.lower():
                                match = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_text_2, re.IGNORECASE)
                                if match:
                                    found_amount = float(match.group(1))
                            else:
                                ui_patterns = [
                                    r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)',
                                    r'(\d+(?:\.\d+)?)\s*\/\-',
                                    r'(?:dividend|int\s*div)\s+of\s+(\d+(?:\.\d+)?)',
                                    r'(?:dividend|int\s*div).*?\s+(\d+(?:\.\d+)?)\s+per'
                                ]
                                for pat in ui_patterns:
                                    matches = re.findall(pat, _clean_text_2, re.IGNORECASE)
                                    if matches:
                                        found_amount = sum(float(m) for m in matches)
                                        break

                            if found_amount:
                                if 'interim' in text_to_search.lower() or 'intdiv' in text_to_search.lower() or 'int div' in text_to_search.lower(): found_type = 'Interim'
                                elif 'findiv' in text_to_search.lower() or 'fin div' in text_to_search.lower() or 'final' in text_to_search.lower(): found_type = 'Final'
                                elif 'special' in text_to_search.lower(): found_type = 'Special'

                        if (found_amount is None or found_record_date is None) and bm_date_obj_check and bm_date_obj_check == trade_date:
                            attachment_url = str(item.get('ATTACHMENT', ''))
                            if attachment_url.startswith('http'):
                                pdf_amount, pdf_record_date = extract_amount_from_pdf(attachment_url)
                                if pdf_amount and found_amount is None:
                                    found_amount = pdf_amount
                                if pdf_record_date and found_record_date is None:
                                    found_record_date = pdf_record_date

                        if found_amount:
                            item['EXTRACTED_DIVIDEND_AMOUNT'] = found_amount
                            item['EXTRACTED_DIVIDEND_TYPE'] = found_type
                        if found_record_date:
                            item['EXTRACTED_RECORD_DATE'] = found_record_date

                    enriched_data.append(item)

                # Finally, synthesize standalone announcements (like COALINDIA General Updates for AGM/Record Date) that were missed
                for sym, anns in symbol_announcements.items():
                    for ann in anns:
                        if ann.get('seq_id') in consumed_announcements:
                            continue

                        subj = str(ann.get('subject', '')).lower()
                        desc = str(ann.get('desc', '')).lower()
                        attchmntText = str(ann.get('attchmntText', '')).lower()

                        has_div = 'dividend' in subj or 'dividend' in desc or 'dividend' in attchmntText
                        has_rd = 'record date' in subj or 'record date' in desc or 'record date' in attchmntText
                        is_agm = 'agm' in subj or 'annual general meeting' in subj or 'agm' in desc or 'annual general meeting' in desc or 'agm' in attchmntText or 'annual general meeting' in attchmntText

                        if has_div or has_rd or is_agm:
                            found_amount = None
                            found_record_date = None
                            found_type = 'Final'

                            text_lower = attchmntText
                            if 'interim' in text_lower or 'intdiv' in text_lower: found_type = 'Interim'
                            elif 'final' in text_lower or 'findiv' in text_lower: found_type = 'Final'
                            elif 'special' in text_lower: found_type = 'Special'

                            xbrl_matches = re.findall(r'<[^>]*Dividend[^>]*>.*?Rs\.?\s*(\d+(?:\.\d+)?).*?</[^>]*>', attchmntText, re.IGNORECASE)
                            if not xbrl_matches:
                                xbrl_matches = re.findall(r'<[^>]*Dividend[^>]*>.*?(\d+(?:\.\d+)?).*?</[^>]*>', attchmntText, re.IGNORECASE)
                            if xbrl_matches:
                                found_amount = sum(float(m) for m in xbrl_matches)

                            bm_purpose = "General Updates"
                            if is_agm:
                                found_type = 'AGM'
                                bm_purpose = 'Annual General Meeting'
                                if 'dateofannualgeneralmeeting' in attchmntText:
                                    agm_date_match = re.search(r'<[^>]*DateOfAnnualGeneralMeeting[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}).*?</[^>]*>', attchmntText, re.IGNORECASE)
                                    if agm_date_match:
                                        bm_purpose += f" - AGM - {agm_date_match.group(1)}"

                            if found_amount is None:
                                _clean_text = re.sub(r'(?:face value|fv|paid-up capital|paid up capital|equity shares? of|shares? of)\s*(?:of\s*)?(?:rs\.?|re\.?|rupees?|inr|[-/]|\s|\u20b9)*\d+(?:\.\d+)?(?:/-)?(?:\s*each)?', '', attchmntText, flags=re.IGNORECASE)
                                if 'including' in _clean_text or 'includes' in _clean_text:
                                    match = re.search(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_text, re.IGNORECASE)
                                    if match: found_amount = float(match.group(1))
                                else:
                                    matches = re.findall(r'(?:rs\.?|re\.?|rupees?|inr|\u20b9)\s*(\d+(?:\.\d+)?)', _clean_text, re.IGNORECASE)
                                    if matches: found_amount = sum(float(m) for m in matches)

                            date_pattern = re.compile(r'(\d{1,2}-[a-zA-Z]{3}-\d{4})')
                            record_date_match = re.search(r'<[^>]*RecordDate[^>]*>.*?(\d{1,2}-[a-zA-Z]{3}-\d{4}).*?</[^>]*>', attchmntText, re.IGNORECASE)
                            if record_date_match:
                                found_record_date = record_date_match.group(1)

                            if not found_record_date:
                                ex_date_match = re.search(r'(?:ex-date|ex date).*?(\d{1,2}-[a-zA-Z]{3}-\d{4})', attchmntText, re.IGNORECASE)
                                if ex_date_match:
                                    found_record_date = ex_date_match.group(1)

                            if not found_record_date:
                                date_match = date_pattern.search(attchmntText)
                                if date_match and 'record date' in text_lower:
                                    found_record_date = date_match.group(1)

                            # Create synthetic board meeting row for this standalone announcement
                            if found_amount or found_record_date or is_agm:
                                try:
                                    dt = datetime.strptime(ann.get('an_dt', '').split(' ')[0], "%d-%b-%Y")
                                    bm_date_str = dt.strftime("%d-%b-%Y")
                                except:
                                    bm_date_str = trade_date.strftime("%d-%b-%Y")

                                syn_item = {
                                    'bm_symbol': sym,
                                    'sm_name': ann.get('sm_name', ''),
                                    'bm_purpose': bm_purpose,
                                    'bm_desc': ann.get('attchmntText', ''),
                                    'bm_date': bm_date_str,
                                    'bm_timestamp': ann.get('an_dt', ''),
                                    'sysTime': ann.get('an_dt', ''),
                                    'ATTACHMENT': ann.get('attchmntFile', ''),
                                    'EXTRACTED_DIVIDEND_AMOUNT': found_amount,
                                    'EXTRACTED_DIVIDEND_TYPE': found_type,
                                    'EXTRACTED_RECORD_DATE': found_record_date
                                }
                                # Prevent duplicates
                                is_dup = False
                                for e in enriched_data:
                                    if e.get('bm_symbol') == syn_item['bm_symbol'] and e.get('EXTRACTED_RECORD_DATE') == syn_item['EXTRACTED_RECORD_DATE'] and e.get('EXTRACTED_DIVIDEND_TYPE') == syn_item['EXTRACTED_DIVIDEND_TYPE']:
                                        is_dup = True
                                        break
                                if not is_dup:
                                    enriched_data.append(syn_item)
"""

# Find the start and end of the block we want to replace
start_marker = "enriched_data = []"
end_marker = "df = pd.DataFrame(enriched_data)"

# Safely extract the original content before start_marker and after end_marker
parts = content.split(start_marker, 1)
if len(parts) == 2:
    before_content = parts[0]
    rest = parts[1]
    subparts = rest.split(end_marker, 1)
    if len(subparts) == 2:
        after_content = subparts[1]

        # Assemble
        new_content = before_content + replacement + "\n                " + end_marker + after_content

        with open('backend/ingest/nse_lib.py', 'w') as f:
            f.write(new_content)
        print("Successfully patched backend/ingest/nse_lib.py")
    else:
        print("Failed to find end marker")
else:
    print("Failed to find start marker")
