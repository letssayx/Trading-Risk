def update_nse_lib():
    with open('backend/ingest/nse_lib.py', 'r') as f:
        content = f.read()

    search_block = """        for attempt in range(1, 4):
            try:
                logger.info(f"Priming NSE session via {self.BASE_URL}... (Attempt {attempt})")
                # Minimal headers for initial handshake often helps
                headers = {
                    'User-Agent': self.HEADERS['User-Agent'],
                    'Accept': '*/*',
                    'Connection': 'keep-alive'
                }
                resp = self.session.get(self.BASE_URL, headers=headers, timeout=30)
                if resp.status_code == 200:
                    self._cookies_primed = True
                    logger.info("Session primed successfully.")
                    return
                else:
                    logger.warning(f"Failed to prime session, status code: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Exception during session priming: {e}")
            time.sleep(2)"""

    replace_block = """        for attempt in range(1, 4):
            try:
                logger.info(f"Priming NSE session via {self.BASE_URL}... (Attempt {attempt})")
                # Minimal headers for initial handshake often helps
                headers = {
                    'User-Agent': self.HEADERS['User-Agent'],
                    'Accept': '*/*',
                    'Connection': 'keep-alive'
                }
                try:
                    resp = self.session.get(self.BASE_URL, headers=headers, timeout=30)
                except Exception as cffi_e:
                    logger.warning(f"cffi session failed to prime, recreating session: {cffi_e}")
                    self.session = cffi_requests.Session(impersonate="chrome110")
                    self.session.headers.update(self.HEADERS)
                    resp = self.session.get(self.BASE_URL, headers=headers, timeout=30)

                if resp.status_code == 200:
                    self._cookies_primed = True
                    logger.info("Session primed successfully.")
                    return
                else:
                    logger.warning(f"Failed to prime session, status code: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Exception during session priming: {e}")
            time.sleep(2)"""

    if search_block in content:
        content = content.replace(search_block, replace_block)
        with open('backend/ingest/nse_lib.py', 'w') as f:
            f.write(content)
        print("Success ensure")
    else:
        print("Failed to find block")

update_nse_lib()
