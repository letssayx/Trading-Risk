import math

def norm_cdf(x):
    """Cumulative distribution function for standard normal distribution"""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def norm_pdf(x):
    """Probability density function for standard normal distribution"""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def bs_d1(S, K, T, r, sigma):
    return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

def bs_d2(d1, T, sigma):
    return d1 - sigma * math.sqrt(T)

def calculate_greeks(S, K, T, r, sigma, is_call):
    d1 = bs_d1(S, K, T, r, sigma)
    d2 = bs_d2(d1, T, sigma)
    pdf_d1 = norm_pdf(d1)

    delta = norm_cdf(d1) if is_call else norm_cdf(d1) - 1.0
    gamma = pdf_d1 / (S * sigma * math.sqrt(T))
    vega = (S * pdf_d1 * math.sqrt(T)) / 100.0

    return {"delta": delta, "gamma": gamma, "vega": vega}

# Test with typical Nifty values based on screenshot
S = 22816.60
K = 21300.0
T = 3.0 / 365.0 # Just guessing a few days based on 27th to 30th? Or maybe 3 years? Screenshot says Date 2026-03-27 Expiry 2026-03-30
r = 0.05
sigma = 0.7068 # 70.68% from screenshot

greeks = calculate_greeks(S, K, T, r, sigma, True)
print(f"Greeks: {greeks}")
