from __future__ import annotations

import FinanceDataReader as fdr
import pandas as pd

from app.services.collectors.base import normalize_ohlcv


def fetch_series(symbol: str, start: str, end: str) -> pd.DataFrame:
    df = fdr.DataReader(symbol, start, end)
    return normalize_ohlcv(df)
