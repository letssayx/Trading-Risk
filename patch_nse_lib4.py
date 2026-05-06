def update_nse_lib():
    with open('backend/ingest/nse_lib.py', 'r') as f:
        content = f.read()

    search_block = """                                                try:
                                                    xbrl_resp = cffi_requests.get(xbrl_api, impersonate="chrome110", timeout=10, headers=self.HEADERS)
                                                except:
                                                    xbrl_resp = self.session.get(xbrl_api, timeout=10)"""

    replace_block = """                                                try:
                                                    xbrl_resp = cffi_requests.get(xbrl_api, impersonate="chrome110", timeout=10, headers=self.HEADERS)
                                                except:
                                                    import requests as std_requests
                                                    xbrl_resp = std_requests.get(xbrl_api, timeout=10, headers=self.HEADERS)"""

    search_block2 = """                                                                try:
                                                                    xml_resp = cffi_requests.get(xml_url, impersonate="chrome110", timeout=10, headers=self.HEADERS)
                                                                except:
                                                                    xml_resp = self.session.get(xml_url, timeout=10)"""

    replace_block2 = """                                                                try:
                                                                    xml_resp = cffi_requests.get(xml_url, impersonate="chrome110", timeout=10, headers=self.HEADERS)
                                                                except:
                                                                    import requests as std_requests
                                                                    xml_resp = std_requests.get(xml_url, timeout=10, headers=self.HEADERS)"""

    search_block3 = """                                    try:
                                        import curl_cffi.requests as cffi_requests
                                        ann_resp = cffi_requests.get(ann_url, impersonate="chrome110", timeout=10, headers=self.HEADERS)
                                    except:
                                        ann_resp = self.session.get(ann_url, timeout=10)"""

    replace_block3 = """                                    try:
                                        import curl_cffi.requests as cffi_requests
                                        ann_resp = cffi_requests.get(ann_url, impersonate="chrome110", timeout=10, headers=self.HEADERS)
                                    except:
                                        import requests as std_requests
                                        ann_resp = std_requests.get(ann_url, timeout=10, headers=self.HEADERS)"""

    search_block4 = """                                            try:
                                                ca_resp = cffi_requests.get(ca_url, impersonate="chrome110", timeout=10, headers=self.HEADERS)
                                                if ca_resp.status_code == 200:"""

    replace_block4 = """                                            try:
                                                ca_resp = cffi_requests.get(ca_url, impersonate="chrome110", timeout=10, headers=self.HEADERS)
                                            except:
                                                import requests as std_requests
                                                ca_resp = std_requests.get(ca_url, timeout=10, headers=self.HEADERS)

                                            try:
                                                if ca_resp.status_code == 200:"""

    search_block5 = """        if use_curl:
            try:
                # Use curl_cffi to bypass Bot protections (e.g. for archives and static CSVs)
                return cffi_requests.get(url, impersonate="chrome110", timeout=30, headers=self.HEADERS)
            except Exception as e:
                logger.error(f"curl_cffi get failed for {url}: {e}")
                return None"""

    replace_block5 = """        if use_curl:
            try:
                # Use curl_cffi to bypass Bot protections (e.g. for archives and static CSVs)
                return cffi_requests.get(url, impersonate="chrome110", timeout=30, headers=self.HEADERS)
            except Exception as e:
                logger.warning(f"curl_cffi get failed for {url}, falling back to standard requests: {e}")
                import requests as std_requests
                try:
                    resp = std_requests.get(url, headers=self.HEADERS, timeout=30)
                    if resp.status_code == 200:
                        return resp
                except:
                    pass
                return None"""

    content = content.replace(search_block, replace_block)
    content = content.replace(search_block2, replace_block2)
    content = content.replace(search_block3, replace_block3)
    content = content.replace(search_block4, replace_block4)
    content = content.replace(search_block5, replace_block5)

    with open('backend/ingest/nse_lib.py', 'w') as f:
        f.write(content)

update_nse_lib()
