import datetime
import numpy as np

def get_doy(d): return d.timetuple().tm_yday

history = [
    datetime.date(2025, 6, 4),
    datetime.date(2023, 7, 28)
]

historical_days = []
for h in history:
    norm_d = datetime.date(2020, h.month, h.day)
    historical_days.append(norm_d.timetuple().tm_yday)

median_doy = int(np.median(historical_days))
norm_median_date = datetime.date(2020, 1, 1) + datetime.timedelta(days=median_doy - 1)

print("Median date:", norm_median_date)
