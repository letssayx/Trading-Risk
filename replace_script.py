import re
with open('backend/ingest/nse_lib.py', 'r') as f:
    content = f.read()

content = re.sub(r"                        if \(found_amount is None or found_record_date is None or found_type == 'Dividend' or \(is_agm and not item.get\('EXTRACTED_AGM_DATE'\)\)\) and bm_date_obj_check:\n                            if bm_date_obj_check != trade_date and \(datetime\.date\.today\(\) - bm_date_obj_check\)\.days > 3:\n                                pass # Prevent scraping infinite past PDFs\n                            else:\n                            attachment_url = str\(item\.get\('ATTACHMENT', ''\)\)",
                 r"                        if (found_amount is None or found_record_date is None or found_type == 'Dividend' or (is_agm and not item.get('EXTRACTED_AGM_DATE'))) and bm_date_obj_check and bm_date_obj_check == trade_date:\n                            attachment_url = str(item.get('ATTACHMENT', ''))",
                 content)

with open('backend/ingest/nse_lib.py', 'w') as f:
    f.write(content)
