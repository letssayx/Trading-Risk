import yfinance as yf
import requests
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
                except Exception:
                    result[name] = {"price": 0.0, "pct_change": 0.0}
        except Exception:
            for name in symbols_dict.keys():
                result[name] = {"price": 0.0, "pct_change": 0.0}
        return result

    @staticmethod
    def get_crypto():
        # Replace ccxt binance with yfinance, as binance API restricts IPs and raises 451.
        symbols = {'bitcoin': 'BTC-USD', 'ethereum': 'ETH-USD', 'solana': 'SOL-USD'}
        return MacroDataFetcher._fetch_yf_batch(symbols)

    @staticmethod
    def get_gift_nifty():
        """Fetch Nifty 50 Index as a proxy for GIFT Nifty using YFinance."""
        try:
            import pandas as pd
            # ^NSEI is Nifty 50. While not exactly GIFT Nifty futures, it's the
            # most reliable live proxy available without paid scrapers.
            data = yf.download('^NSEI', period="5d", progress=False)

            # Yfinance returns a DataFrame where columns might be MultiIndex if not careful,
            # but for a single ticker it's usually flat. Let's handle both.
            if isinstance(data.columns, pd.MultiIndex):
                close_series = data['Close']['^NSEI']
            else:
                close_series = data['Close']

            closes = close_series.dropna().values
            if len(closes) >= 2:
                current = float(closes[-1])
                prev = float(closes[-2])
                pct = ((current - prev) / prev) * 100
                return {"price": current, "pct_change": pct}
            elif len(closes) == 1:
                return {"price": float(closes[0]), "pct_change": 0.0}
        except Exception as e:
            import logging
            logging.error(f"Failed to fetch GIFT Nifty proxy: {e}")
            pass
        return {"price": 0.0, "pct_change": 0.0}

    @staticmethod
    def get_economic_events(days_ahead=7):
        """Fetch high-impact economic events from ForexFactory XML feed, prioritizing India and Central Banks."""
        events = []
        try:
            url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)

                # Priority countries: INR (India), USD (US), JPY (Japan), EUR (Europe), GBP (UK)
                target_countries = ['INR', 'USD', 'JPY', 'EUR', 'GBP', 'CNY']

                # Keywords to prioritize (Monetary policy, GDP, CPI)
                high_priority_keywords = ['rate', 'cpi', 'gdp', 'inflation', 'fed', 'rbi', 'boj', 'ecb', 'minutes', 'pmi', 'employment']

                for event in root.findall('event'):
                    impact = event.find('impact').text if event.find('impact') is not None else ""
                    country = event.find('country').text if event.find('country') is not None else ""
                    title = event.find('title').text if event.find('title') is not None else ""

                    # Always include INR events regardless of impact.
                    # For other target countries, include if Impact is High or Medium+ matches keywords.
                    is_inr = country == 'INR'
                    is_high_impact = impact == 'High' and country in target_countries

                    is_priority_keyword = any(k in title.lower() for k in high_priority_keywords)
                    is_medium_priority = impact == 'Medium' and country in target_countries and is_priority_keyword

                    if is_inr or is_high_impact or is_medium_priority:
                        # Override impact for INR so it always highlights if it's important
                        final_impact = impact
                        if is_inr:
                            final_impact = "High" if is_priority_keyword else "Medium"

                        events.append({
                            "event_date": event.find('date').text + " " + event.find('time').text,
                            "country": country,
                            "event_name": title,
                            "actual": event.find('actual').text if event.find('actual') is not None else "",
                            "forecast": event.find('forecast').text if event.find('forecast') is not None else "",
                            "previous": event.find('previous').text if event.find('previous') is not None else "",
                            "impact": final_impact
                        })
        except Exception:
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
