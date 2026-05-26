with open('backend/web/api/data/board_meeting_routes.py', 'r') as f:
    content = f.read()

old_ssrf = """        if not xml_url.startswith("http"):
            raise HTTPException(status_code=400, detail="Only HTTP/HTTPS URLs are supported for security reasons.")"""

new_ssrf = """        if not xml_url.startswith("http://") and not xml_url.startswith("https://"):
            raise HTTPException(status_code=400, detail="Only HTTP/HTTPS URLs are supported for security reasons.")
        if "nseindia.com" not in xml_url:
            raise HTTPException(status_code=400, detail="For security reasons, only URLs from nseindia.com are permitted.")"""

content = content.replace(old_ssrf, new_ssrf)

with open('backend/web/api/data/board_meeting_routes.py', 'w') as f:
    f.write(content)
