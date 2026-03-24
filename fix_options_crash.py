with open("backend/web/api/data/options_routes.py", "r") as f:
    content = f.read()

old_options = """            if not latest_fo_date_row:
                return {"data": {}, "expiries": [], "spot_price": 0.0}"""

new_options = """            if not latest_fo_date_row:
                return {"data": [], "expiries": [], "spot_price": 0.0}"""

content = content.replace(old_options, new_options)

old_options2 = """        if not valid_expiries:
            return {"data": {}, "expiries": [], "spot_price": spot_price}"""

new_options2 = """        if not valid_expiries:
            return {"data": [], "expiries": [], "spot_price": spot_price}"""

content = content.replace(old_options2, new_options2)

with open("backend/web/api/data/options_routes.py", "w") as f:
    f.write(content)
