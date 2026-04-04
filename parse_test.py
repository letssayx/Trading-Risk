import json

def generate_mock_data():
    results = []

    # Simulating values to trigger exceptions (like round() on None)

    # 1. Null handling check
    atm_iv = None
    try:
        round(atm_iv, 2) if atm_iv else None
    except Exception as e:
        print("Error in atm_iv:", e)

    # 2. adv_metrics values
    adv_metrics = {
        "oi_chg_30d": None, "price_chg_30d": 0,
        "oi_chg_60d": 0, "price_chg_60d": 0,
        "oi_chg_90d": 0, "price_chg_90d": 0,
        "oi_chg_252d": 0, "price_chg_252d": 0,
        "oi_chg_500d": 0, "price_chg_500d": 0
    }

    try:
        # this is what the code does
        res = {k: round(v, 2) for k, v in adv_metrics.items()}
    except Exception as e:
        print("Error in adv_metrics:", e)

    return "Done"

generate_mock_data()
