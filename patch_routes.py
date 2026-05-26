import re

with open('backend/web/api/data/board_meeting_routes.py', 'r') as f:
    content = f.read()

new_content = content.replace(
    'class OverrideXMLRequest(BaseModel):',
    'from fastapi import File, Form, UploadFile\n\nclass OverrideXMLRequest(BaseModel):'
)

new_content = new_content.replace(
    'def override_board_meeting_xml(req: OverrideXMLRequest, db: Session = Depends(get_db)):',
    '''def override_board_meeting_xml(
    symbol: str = Form(...),
    meeting_date: str = Form(...),
    xml_url: str = Form(...),
    db: Session = Depends(get_db)
):'''
)

new_content = new_content.replace(
    'req.meeting_date', 'meeting_date'
).replace(
    'req.symbol', 'symbol'
).replace(
    'req.xml_url', 'xml_url'
)

with open('backend/web/api/data/board_meeting_routes.py', 'w') as f:
    f.write(new_content)
