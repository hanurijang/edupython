from __future__ import annotations

import pandas as pd

from app.services.collectors.base import normalize_ohlcv


def fetch_series(symbol: str, start: str, end: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError('yfinance 패키지가 필요합니다.') from exc

    df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return normalize_ohlcv(df)
