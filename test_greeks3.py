import numpy as np
import warnings
from scipy.stats import norm

warnings.simplefilter('always', RuntimeWarning)

S = 100.0
K = 100.0
T = 0.5
r = 0.05
sigma = 1e160

d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
print(d1)
