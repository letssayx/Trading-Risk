import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, date
import logging
from io import StringIO

logger = logging.getLogger(__name__)

def fetch_arihant_fii_dii(trade_date: date) -> pd.DataFrame:
    url = "https://www.arihantcapital.com/derivatives/fii-dii-trading-activities"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    try:
        session = requests.Session()

        # 1. Fetch the initial page to get FII data and ASP.NET viewstates
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        records = []

        # Parse FII from default page load
        tables = soup.find_all('table')
        if tables:
            try:
                fii_df = pd.read_html(StringIO(str(tables[0])), flavor='bs4')[0]
                for _, row in fii_df.iterrows():
                    row_date_str = str(row.iloc[0]).strip()
                    try:
                        parsed_date = pd.to_datetime(row_date_str, format='mixed', dayfirst=True).date()
                        if parsed_date == trade_date:
                            records.append({
                                'trade_date': parsed_date,
                                'category': 'FII',
                                'buy_value': float(str(row.iloc[1]).replace(',', '')),
                                'sell_value': float(str(row.iloc[2]).replace(',', '')),
                                'net_value': float(str(row.iloc[3]).replace(',', ''))
                            })
                            break
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"Error parsing Arihant FII table: {e}")

        # 2. Extract hidden fields to simulate a form submission for DII
        viewstate = soup.find(id="__VIEWSTATE")
        viewstategenerator = soup.find(id="__VIEWSTATEGENERATOR")

        if viewstate and viewstategenerator:
            payload = {
                "__EVENTTARGET": "ctl00$ContentPlaceHolder1$ddlSubCategory",
                "__EVENTARGUMENT": "",
                "__LASTFOCUS": "",
                "__VIEWSTATE": viewstate['value'],
                "__VIEWSTATEGENERATOR": viewstategenerator['value'],
                "ctl00$ContentPlaceHolder1$cattypeid": "cash",
                "ctl00$ContentPlaceHolder1$fosubCatid": "index",
                "ctl00$ContentPlaceHolder1$ddlSubCategory": "DII"
            }

            resp_dii = session.post(url, data=payload, headers=headers, timeout=10)
            soup_dii = BeautifulSoup(resp_dii.content, 'html.parser')
            tables_dii = soup_dii.find_all('table')

            if tables_dii:
                try:
                    dii_df = pd.read_html(StringIO(str(tables_dii[0])), flavor='bs4')[0]
                    for _, row in dii_df.iterrows():
                        row_date_str = str(row.iloc[0]).strip()
                try:
                    parsed_date = pd.to_datetime(row_date_str, format='mixed', dayfirst=True).date()
                    if parsed_date == trade_date:
                        records.append({
                            'trade_date': parsed_date,
                            'category': 'FII',
                            'buy_value': float(str(row.iloc[1]).replace(',', '')),
                            'sell_value': float(str(row.iloc[2]).replace(',', '')),
                            'net_value': float(str(row.iloc[3]).replace(',', ''))
                        })
                        break
                    except Exception:
                        continue
                except Exception as e:
                    logger.warning(f"Error parsing Arihant DII table: {e}")
        else:
            logger.warning("Could not find ASP.NET VIEWSTATE tokens on Arihant page, skipping DII fetch.")

        if not records:
            logger.warning(f"No Arihant FII/DII records found for {trade_date}")
            return pd.DataFrame()

        return pd.DataFrame(records)

    except Exception as e:
        logger.error(f"Error scraping Arihant FII/DII data: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = fetch_arihant_fii_dii(datetime(2026, 3, 24).date())
    print(df)
