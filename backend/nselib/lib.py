"""
backend/nselib/lib.py
"""
import logging
import requests
import time

from .constants import HEADERS, BASE_URL

logger = logging.getLogger(__name__)

class NseSession:
    """
    Session manager for NSE requests.
    Handles cookie priming, retries, and headers.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._cookies_primed = False

    def _ensure_session(self):
        """Prime cookies if not already done."""
        if self._cookies_primed:
            return

        try:
            logger.info(f"Priming NSE session via {BASE_URL}...")
            # Minimal headers for initial handshake often helps
            headers = {
                'User-Agent': HEADERS['User-Agent'],
                'Accept': '*/*',
                'Connection': 'keep-alive'
            }
            resp = self.session.get(BASE_URL, headers=headers, timeout=10)
            if resp.status_code == 200:
                self._cookies_primed = True
                logger.info("Session primed successfully.")
            else:
                logger.warning(f"Session prime failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"Session prime error: {e}")

    def get(self, url: str, params: dict = None, timeout: int = 30) -> requests.Response:
        """Execute GET request with session handling and retries."""
        self._ensure_session()

        # Ensure Referer is set for API calls if needed
        if 'api' in url and 'Referer' not in self.session.headers:
            self.session.headers['Referer'] = BASE_URL

        try:
            resp = self.session.get(url, params=params, timeout=timeout)

            # Retry on 401/403 once by re-priming session
            if resp.status_code in (401, 403):
                logger.warning(f"Got {resp.status_code} for {url}, re-priming session...")
                self._cookies_primed = False
                self.session.cookies.clear()
                self._ensure_session()
                # Wait briefly
                time.sleep(1)
                resp = self.session.get(url, params=params, timeout=timeout)

            return resp
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise
