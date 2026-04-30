import re

with open('backend/web/api/data/view_routes.py', 'r') as f:
    content = f.read()

diff_search = """        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            sh_section = soup.find('section', id='shareholding')
            if sh_section:
                table = sh_section.find('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = [col.text.strip() for col in row.find_all(['th', 'td'])]
                        if not cols: continue
                        label = cols[0].replace('+', '').strip().lower()
                        if len(cols) > 1:
                            val_str = cols[-1].replace('%', '')
                            try:
                                val = float(val_str)
                                if label == 'promoters':
                                    promoter_pct = val
                                elif label == 'fiis':
                                    fii_pct = val
                                elif label == 'diis':
                                    dii_pct = val
                                elif label == 'public':
                                    retail_pct = val
                            except ValueError:
                                pass

        total_shares = 0
        try:
            ticker = yf.Ticker(f"{symbol.upper()}.NS")
            total_shares = ticker.fast_info.get('shares', 0)
            if not total_shares:
                total_shares = ticker.info.get('sharesOutstanding', 0)
        except Exception:
            pass

        return {
            "symbol": symbol.upper(),
            "promoter_holding": promoter_pct,
            "fii_holding": fii_pct,
            "dii_holding": dii_pct,
            "retail_holding": 0, # Cannot reliably distinguish from screener fallback
            "public_holding": retail_pct,
            "total_outstanding": int(total_shares) if total_shares else 0,

            # Since absolute values aren't known, don't return them so frontend falls back to pct math
        }
    except Exception as e:
        logger.error(f"Error fetching shareholding for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))"""

diff_replace = """        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                xbrl_url = data[0].get('xbrl')
                if xbrl_url:
                    res_xml = session.get(xbrl_url, headers=headers, timeout=5)
                    if res_xml.status_code == 200:
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(res_xml.text)
                        def get_shares(context_id):
                            for elem in root:
                                tag_name = elem.tag.split('}')[-1]
                                if tag_name == 'NumberOfShares' and elem.attrib.get('contextRef') == context_id:
                                    return float(elem.text)
                            return 0

                        promoter = get_shares('ShareholdingOfPromoterAndPromoterGroup_ContextI')
                        fii = (
                            get_shares('InstitutionsForeignPortfolioInvestorCategoryOne_ContextI') +
                            get_shares('InstitutionsForeignPortfolioInvestorCategoryTwo_ContextI') +
                            get_shares('ForeignNationals_ContextI') +
                            get_shares('ForeignCompanies_ContextI')
                        )
                        if fii == 0:
                            fii = get_shares('InstitutionsForeign_ContextI')
                            if fii > 0:
                                fii -= get_shares('OverseasDepositories_ContextI')

                        dii = (
                            get_shares('MutualFundsOrUTI_ContextI') +
                            get_shares('InsuranceCompanies_ContextI') +
                            get_shares('Banks_ContextI') +
                            get_shares('AlternativeInvestmentFunds_ContextI') +
                            get_shares('ProvidentFundsOrPensionFunds_ContextI') +
                            get_shares('NBFCsRegisteredWithRBI_ContextI')
                        )
                        if dii == 0:
                            dii = get_shares('InstitutionsDomestic_ContextI')

                        others = get_shares('EmployeeBenefitsTrusts_ContextI')
                        if others == 0:
                            others = get_shares('SharesHeldByNonPromoterNonPublicShareholders_ContextI')

                        retail_less_200k = get_shares('ResidentIndividualShareholdersHoldingNominalShareCapitalUpToRsTwoLakh_ContextI')

                        public_gt_200k = (
                            get_shares('ResidentIndividualShareholdersHoldingNominalShareCapitalInExcessOfRsTwoLakh_ContextI') +
                            get_shares('NonResidentIndians_ContextI') +
                            get_shares('BodiesCorporate_ContextI') +
                            get_shares('OtherNonInstitutions_ContextI')
                        )
                        if public_gt_200k == 0:
                            non_inst = get_shares('NonInstitutions_ContextI')
                            if non_inst > 0:
                                public_gt_200k = non_inst - retail_less_200k

                        adr_shares = get_shares('OverseasDepositories_ContextI')

                        total_out = get_shares('ShareholdingPattern_ContextI')

                        if total_out > 0:
                            return {
                                "symbol": symbol.upper(),
                                "promoter_holding": round((promoter/total_out)*100, 2),
                                "fii_holding": round((fii/total_out)*100, 2),
                                "dii_holding": round((dii/total_out)*100, 2),
                                "others_holding": round((others/total_out)*100, 2),
                                "retail_holding": round((retail_less_200k/total_out)*100, 2),
                                "public_holding": round((public_gt_200k/total_out)*100, 2),
                                "adr_holding": round((adr_shares/total_out)*100, 2),
                                "total_outstanding": int(total_out),
                                "promoter_shares": int(promoter),
                                "fii_shares": int(fii),
                                "dii_shares": int(dii),
                                "others_shares": int(others),
                                "retail_shares": int(retail_less_200k),
                                "public_shares": int(public_gt_200k),
                                "adr_shares": int(adr_shares)
                            }
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="NSE shareholding fetch failed.")
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Error fetching shareholding for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"NSE shareholding fetch error: {str(e)}")"""

new_content = content.replace(diff_search, diff_replace)

# Now for the requests/yf stuff at the top of the function
search_2 = """        # Fallback to Screener.in if NSE fails
        from bs4 import BeautifulSoup
        import yfinance as yf

        url = f"https://www.screener.in/company/{symbol.upper()}/consolidated/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            url = f"https://www.screener.in/company/{symbol.upper()}/"
            response = requests.get(url, headers=headers)

        promoter_pct = 0.0
        fii_pct = 0.0
        dii_pct = 0.0
        retail_pct = 0.0"""

replace_2 = """        url = f"https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol={symbol.upper()}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        session = requests.Session()
        session.get('https://www.nseindia.com', headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)"""

new_content = new_content.replace(search_2, replace_2)

# Now fix the FUT query
search_3 = """        # We need the latest trade date in BhavcopyFO for this symbol to get active futures
        latest_fo_date_record = db.query(BhavcopyFO).filter(
            BhavcopyFO.ticker_symb == symbol.upper(),
            BhavcopyFO.instrument_type.like('FUT%')
        ).order_by(BhavcopyFO.trade_date.desc()).first()

        if latest_fo_date_record:
            latest_fo_date = latest_fo_date_record.trade_date
            futures = db.query(BhavcopyFO).filter(
                BhavcopyFO.ticker_symb == symbol.upper(),
                BhavcopyFO.trade_date == latest_fo_date,
                BhavcopyFO.instrument_type.like('FUT%')
            ).order_by(BhavcopyFO.expiry_date.asc()).limit(3).all()"""

replace_3 = """        # We need the latest trade date in BhavcopyFO for this symbol to get active futures
        latest_fo_date_record = db.query(BhavcopyFO).filter(
            BhavcopyFO.ticker_symb == symbol.upper(),
            BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX'])
        ).order_by(BhavcopyFO.trade_date.desc()).first()

        if latest_fo_date_record:
            latest_fo_date = latest_fo_date_record.trade_date
            futures = db.query(BhavcopyFO).filter(
                BhavcopyFO.ticker_symb == symbol.upper(),
                BhavcopyFO.trade_date == latest_fo_date,
                BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX'])
            ).order_by(BhavcopyFO.expiry_date.asc()).limit(3).all()"""

new_content = new_content.replace(search_3, replace_3)

# And remove the try except that wrapped the initial NSE fetch since we replaced it with the session block
search_4 = """    try:
        url = f"https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol={symbol.upper()}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        session = requests.Session()
        session.get('https://www.nseindia.com', headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)

        if response.status_code == 200:"""

replace_4 = """    try:
        url = f"https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol={symbol.upper()}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        session = requests.Session()
        session.get('https://www.nseindia.com', headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)"""

# Actually, the original file had this block:
search_5 = """    try:
        # Try fetching from NSE API first for absolute exact share counts
        import requests
        import xml.etree.ElementTree as ET

        url = f"https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol={symbol.upper()}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        session = requests.Session()
        session.get('https://www.nseindia.com', headers=headers, timeout=5)
        res = session.get(url, headers=headers, timeout=5)

        if res.status_code == 200:
            data = res.json()
            if data and isinstance(data, list):
                xbrl_url = data[0].get('xbrl')
                if xbrl_url:
                    res_xml = session.get(xbrl_url, headers=headers, timeout=5)
                    if res_xml.status_code == 200:
                        root = ET.fromstring(res_xml.text)

                        def get_shares(context_id):
                            for elem in root:
                                tag_name = elem.tag.split('}')[-1]
                                if tag_name == 'NumberOfShares' and elem.attrib.get('contextRef') == context_id:
                                    return float(elem.text)
                            return 0

                        promoter = get_shares('ShareholdingOfPromoterAndPromoterGroup_ContextI')
                        fii = get_shares('InstitutionsForeign_ContextI')
                        dii = get_shares('InstitutionsDomestic_ContextI')
                        retail_less_200k = get_shares('ResidentIndividualShareholdersHoldingNominalShareCapitalUpToRsTwoLakh_ContextI')
                        public_gt_200k = get_shares('ResidentIndividualShareholdersHoldingNominalShareCapitalInExcessOfRsTwoLakh_ContextI')
                        total_out = get_shares('ShareholdingPattern_ContextI')

                        if total_out > 0:
                            return {
                                "symbol": symbol.upper(),
                                "promoter_holding": round((promoter/total_out)*100, 2),
                                "fii_holding": round((fii/total_out)*100, 2),
                                "dii_holding": round((dii/total_out)*100, 2),
                                "retail_holding": round((retail_less_200k/total_out)*100, 2),
                                "public_holding": round((public_gt_200k/total_out)*100, 2),
                                "total_outstanding": int(total_out),

                                # Absolute values
                                "promoter_shares": int(promoter),
                                "fii_shares": int(fii),
                                "dii_shares": int(dii),
                                "retail_shares": int(retail_less_200k),
                                "public_shares": int(public_gt_200k)
                            }
        except Exception as e:
            logger.warning(f"Failed to fetch XBRL from NSE for {symbol}: {e}")"""

replace_5 = """    try:
        # Fetching strictly from NSE API
        import requests

        url = f"https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol={symbol.upper()}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        session = requests.Session()
        session.get('https://www.nseindia.com', headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)"""

new_content = new_content.replace(search_5, replace_5)

with open('backend/web/api/data/view_routes.py', 'w') as f:
    f.write(new_content)
