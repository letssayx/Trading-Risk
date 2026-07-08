"""NSE Session Manager - Aligned with nselib v2.4.3 Strategy"""
import requests
import time
import logging
from typing import Optional
from backend.config.defaults.nse import REQUEST_HEADERS, NSE_MAIN_URL, REQUEST_TIMEOUT, RATE_LIMIT_DELAY

logger = logging.getLogger(__name__)

class NSESessionManager:
    """
    Session manager that mimics nselib's behavior:
    1. Sets strict headers (User-Agent, Accept, Sec-Fetch-*).
    2. Primes cookies by visiting the home page first.
    3. Sets Referer header for subsequent data requests.
    """

    def __init__(self):
        self.session = requests.Session()
        # Set default headers for all requests
        self.session.headers.update(REQUEST_HEADERS)
        self.last_request_time = 0
        self._ensure_cookies()

    def _ensure_cookies(self):
        """
        Visits the NSE main page to establish session cookies.
        Uses a minimal header set initially to mimic a fresh browser visit.
        """
        try:
            logger.info(f"Priming NSE session via {NSE_MAIN_URL}...")

            # Temporary header manipulation for the handshake
            # nselib uses minimal headers for the first request
            original_headers = self.session.headers.copy()
            self.session.headers.clear()
            self.session.headers.update({
                'User-Agent': REQUEST_HEADERS['User-Agent'],
                'Accept': '*/*',
                'Connection': 'keep-alive'
            })

            resp = self.session.get(NSE_MAIN_URL, timeout=5)

            # Restore full headers
            self.session.headers.update(original_headers)

            if resp.status_code == 200:
                logger.debug(f"NSE session primed. Cookies: {list(self.session.cookies.keys())}")
            else:
                 logger.warning(f"NSE session prime failed: HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"NSE session prime error: {e}")

    def _rate_limit(self):
        """Ensure we don't hit rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        GET request with rate limiting, header management, and error handling.
        """
        self._rate_limit()

        # Ensure cookies exist (retry priming if session expired/cleared)
        if not self.session.cookies:
            logger.info("Session cookies missing, re-priming...")
            self._ensure_cookies()

        # Prepare headers for this specific request
        # NSE data endpoints usually require the Referer to be the home page
        req_headers = kwargs.pop('headers', {}).copy()
        if 'Referer' not in req_headers:
            req_headers['Referer'] = NSE_MAIN_URL

        # Merge with session headers (priority to req_headers)
        # Note: requests.Session.request() merges automatically, but we want to ensure Referer is set

        try:
            resp = self.session.get(
                url,
                headers=req_headers,
                timeout=kwargs.get('timeout', REQUEST_TIMEOUT),
                **kwargs
            )
            self.last_request_time = time.time()

            # If we get a 401/403, it might be a stale session. Try one refresh.
            if resp.status_code in (401, 403):
                logger.warning(f"HTTP {resp.status_code} encountered. Refreshing session and retrying...")
                self.session.cookies.clear()
                self._ensure_cookies()
                resp = self.session.get(
                    url,
                    headers=req_headers,
                    timeout=kwargs.get('timeout', REQUEST_TIMEOUT),
                    **kwargs
                )
                self.last_request_time = time.time()

            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code}: {url}")
                # We return the response object even on error so the caller can inspect status_code

            return resp

        except requests.exceptions.Timeout:
            logger.error(f"Timeout: {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error: {url}")
            return None
        except Exception as e:
            logger.error(f"Request failed: {url} - {e}")
            return None
