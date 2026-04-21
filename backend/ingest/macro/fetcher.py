import yfinance as yf
import ccxt
import datetime
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

class MacroDataFetcher:
    """Fetches global macro, crypto, and economic calendar data."""

    @staticmethod
    def get_us_markets():
        symbols = {'sp500': '^GSPC', 'nasdaq': '^IXIC', 'dow': '^DJI'}
        return MacroDataFetcher._fetch_yf_batch(symbols)

    @staticmethod
    def get_asia_markets():
        symbols = {'nikkei': '^N225', 'hangseng': '^HSI', 'kospi': '^KS11'}
        return MacroDataFetcher._fetch_yf_batch(symbols)

    @staticmethod
    def get_macro_commodities():
        symbols = {'dxy': 'DX-Y.NYB', 'crude': 'BZ=F', 'gold': 'GC=F', 'silver': 'SI=F'}
        return MacroDataFetcher._fetch_yf_batch(symbols)

    @staticmethod
    def _fetch_yf_batch(symbols_dict):
        result = {}
        try:
            tickers = list(symbols_dict.values())
            data = yf.download(tickers, period="5d", progress=False)

            for name, ticker in symbols_dict.items():
                try:
                    if len(tickers) == 1:
                        close_series = data['Close']
                    else:
                        close_series = data['Close'][ticker]

                    closes = close_series.dropna().values
                    if len(closes) >= 2:
                        current = closes[-1]
                        prev = closes[-2]
                        pct = ((current - prev) / prev) * 100
                        result[name] = {"price": float(current), "pct_change": float(pct)}
                    elif len(closes) == 1:
                        result[name] = {"price": float(closes[0]), "pct_change": 0.0}
                    else:
                        result[name] = {"price": 0.0, "pct_change": 0.0}
                except Exception as e:
                    result[name] = {"price": 0.0, "pct_change": 0.0}
        except Exception as e:
            for name in symbols_dict.keys():
                result[name] = {"price": 0.0, "pct_change": 0.0}
        return result

    @staticmethod
    def get_crypto():
        result = {}
        try:
            exchange = ccxt.binance()
            symbols = {'bitcoin': 'BTC/USDT', 'ethereum': 'ETH/USDT', 'solana': 'SOL/USDT'}
            for name, symbol in symbols.items():
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    price = ticker.get('last', 0.0)
                    pct = ticker.get('percentage', 0.0)
                    result[name] = {"price": float(price), "pct_change": float(pct)}
                except:
                    result[name] = {"price": 0.0, "pct_change": 0.0}
        except Exception as e:
            for name in ['bitcoin', 'ethereum', 'solana']:
                result[name] = {"price": 0.0, "pct_change": 0.0}
        return result

    @staticmethod
    def get_gift_nifty():
        """Scrape GIFT Nifty from a public source (Moneycontrol or similar)"""
        # Note: GIFT Nifty is notoriously hard to scrape reliably as it's heavily protected by captchas on most Indian sites.
        # We will attempt a standard request, but fallback gracefully.
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        try:
            # Example fallback URL
            url = "https://www.google.com/finance/quote/NIFTY50_F:NSE"
            # As a simpler alternative since this is an Institutional Shell, we can derive an approximation
            # or allow the user to input it in the UI. For now, we return 0.0 to let the UI know it needs manual input.
            return {"price": 0.0, "pct_change": 0.0, "status": "manual_input_required"}
        except:
            return {"price": 0.0, "pct_change": 0.0}

    @staticmethod
    def get_economic_events(days_ahead=7):
        """Fetch high-impact economic events from ForexFactory XML feed."""
        events = []
        try:
            url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                target_countries = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'CNY']

                for event in root.findall('event'):
                    impact = event.find('impact').text if event.find('impact') is not None else ""
                    country = event.find('country').text if event.find('country') is not None else ""

                    if impact == "High" and country in target_countries:
                        events.append({
                            "event_date": event.find('date').text + " " + event.find('time').text,
                            "country": country,
                            "event_name": event.find('title').text,
                            "actual": event.find('actual').text if event.find('actual') is not None else "",
                            "forecast": event.find('forecast').text if event.find('forecast') is not None else "",
                            "previous": event.find('previous').text if event.find('previous') is not None else "",
                            "impact": impact
                        })
        except Exception as e:
            pass
        return events

    @staticmethod
    def build_snapshot():
        """Aggregates all macro data into a single dictionary."""
        snapshot = {}
        snapshot.update(MacroDataFetcher.get_us_markets())
        snapshot.update(MacroDataFetcher.get_asia_markets())
        snapshot.update(MacroDataFetcher.get_macro_commodities())
        snapshot.update(MacroDataFetcher.get_crypto())

        # Gift Nifty requires special handling or manual input
        snapshot['gift_nifty'] = MacroDataFetcher.get_gift_nifty()

        return snapshot
