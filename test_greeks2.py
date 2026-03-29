import math

# Using the NIFTY example, spot = 22816.60
# For the 21300 Call, Delta is 0.87, Vega is 4.45
# Our test script outputs:
# Delta = 0.866 (rounds to 0.87)
# Vega = 4.447 (rounds to 4.45)
# Gamma = 0.000147. If formatted to 2 decimal places in UI (like `fmt(c.gamma)` might do), it becomes 0.00.

# What does fmt() do in JS?
