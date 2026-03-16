import numpy as np
import warnings

def test_overflow():
    warnings.simplefilter('always', RuntimeWarning)

    S = 100.0
    K = 100.0
    T = 0.5
    r = 0.05
    sigma = 1000.0 # very large sigma

    try:
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        print("d1:", d1)
    except Exception as e:
        print("Exception:", e)

test_overflow()
