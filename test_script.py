import re

pdf_text = """
the 52nd Annual General Meeting (AGM) of the Company will be held through Video
Conferencing/Other Audio-Visual Means (VC/OAVM) on Monday, the 31st August, 2026 at
11:00 A.M.
"""
agm_patterns = [
    r'(?:annual general meeting|agm).*?to be held on.*?\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b',
    r'(?:annual general meeting|agm).*?scheduled.*?on.*?\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b',
    r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b.*?(?:annual general meeting|agm)',
    r'(?:agm|annual general meeting).*?\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b'
]
for pat in agm_patterns:
    agm_m = re.search(pat, pdf_text, re.IGNORECASE | re.DOTALL)
    if agm_m:
        print(agm_m.group(1))
        break
