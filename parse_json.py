import json

data = [
  {
    "bcEndDate": "-",
    "bcStartDate": "-",
    "caBroadcastDate": "13-May-2024",
    "comp": "DLF Limited",
    "exDate": "31-Jul-2024",
    "faceVal": "2",
    "ind": "-",
    "isin": "INE271C01023",
    "ndEndDate": "-",
    "ndStartDate": "-",
    "recDate": "31-Jul-2024",
    "series": "EQ",
    "subject": "Dividend - Rs 5 Per Share",
    "symbol": "DLF"
  }
]
print(json.dumps(data, indent=2))
