with open('backend/web/api/data/board_meeting_routes.py', 'r') as f:
    content = f.read()

new_content = content.replace(
'''def override_board_meeting_xml(
    symbol: str = Form(...),
    meeting_date: str = Form(...),
    xml_url: str = Form(...),
    db: Session = Depends(get_db)
):''',
'''def override_board_meeting_xml(
    symbol: str = Form(...),
    meeting_date: str = Form(...),
    xml_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):'''
)

new_content = new_content.replace(
'''    # Fetch XML content
    if not xml_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Only HTTP/HTTPS URLs are supported for security reasons.")

    try:
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'accept-language': 'en-US,en;q=0.9',
        }
        resp = requests.get(xml_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch XML URL. HTTP Status: {resp.status_code}")
        xml_text = resp.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching remote XML: {e}")''',
'''    # Fetch XML content
    xml_text = ""
    if file:
        xml_text = file.file.read().decode("utf-8")
    elif xml_url:
        if not xml_url.startswith("http"):
            raise HTTPException(status_code=400, detail="Only HTTP/HTTPS URLs are supported for security reasons.")
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'accept-language': 'en-US,en;q=0.9',
            }
            resp = requests.get(xml_url, headers=headers, timeout=10)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to fetch XML URL. HTTP Status: {resp.status_code}")
            xml_text = resp.text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error fetching remote XML: {e}")
    else:
        raise HTTPException(status_code=400, detail="Either xml_url or an uploaded file must be provided.")'''
)

with open('backend/web/api/data/board_meeting_routes.py', 'w') as f:
    f.write(new_content)
