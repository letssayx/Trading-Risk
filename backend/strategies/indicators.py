import pandas as pd
import numpy as np

def calc_atr(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    Calculates Average True Range (ATR) or 'N'.
    Assumes df has 'high', 'low', 'close'.
    """
    high = df['high']
    low = df['low']
    close = df['close'].shift(1)

    tr1 = high - low
    tr2 = abs(high - close)
    tr3 = abs(low - close)

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Use exponential moving average for smoothing (standard Turtle is simplified, but Wilder is common)
    # Turtle original used simple average for first, then (PrevN * (period-1) + TR) / period
    # We will use Wilder's Smoothing which is standard in pandas ewm(alpha=1/period)
    df['ATR'] = tr.ewm(alpha=1/period, adjust=False).mean()
    return df

def calc_donchian(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    Calculates Donchian Channels (N-day High/Low).
    The 'Breakout' level is the High of the PREVIOUS 'period' days.
    """
    # Shift by 1 because we break out of the *previous* N days range
    df[f'High_{period}'] = df['high'].rolling(window=period).max().shift(1)
    df[f'Low_{period}'] = df['low'].rolling(window=period).min().shift(1)
    return df
