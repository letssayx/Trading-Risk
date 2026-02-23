"""NSE Session Manager - Simplified from nselib v2.4.3"""
import requests
import time
import logging
from typing import Optional
from backend.config.defaults.nse import REQUEST_HEADERS, NSE_MAIN_URL, REQUEST_TIMEOUT, RATE_LIMIT_DELAY

logger = logging.getLogger(__name__)

class NSESessionManager:
    """Simplified session manager"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUEST_HEADERS)
        self.last_request_time = 0
        self._initialize()

    def _initialize(self):
        """Initialize session - nselib style"""
        try:
            # Just visit main page to get cookies
            resp = self.session.get(NSE_MAIN_URL, timeout=10)
            if resp.status_code == 200:
                logger.debug("NSE session initialized")
        except Exception as e:
            logger.warning(f"Session init warning: {e}")

    def _rate_limit(self):
        """Ensure we don't hit rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """GET request with rate limiting and error handling"""
        self._rate_limit()

        try:
            resp = self.session.get(
                url,
                timeout=kwargs.get('timeout', REQUEST_TIMEOUT),
                **kwargs
            )
            self.last_request_time = time.time()

            if resp.status_code == 200:
                return resp
            elif resp.status_code == 404:
                logger.debug(f"File not found: {url}")
                return None
            elif resp.status_code == 403:
                logger.error(f"Access forbidden (403). Headers may need update.")
                return None
            else:
                logger.warning(f"HTTP {resp.status_code}: {url}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Timeout: {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error: {url}")
            return None
        except Exception as e:
            logger.error(f"Request failed: {url} - {e}")
            return None
