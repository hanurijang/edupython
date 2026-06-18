from __future__ import annotations

import pandas as pd

from app.services.collectors.base import normalize_ohlcv
from app.services.collectors.fdr_collector import fetch_series as fetch_fdr_series
from app.services.collectors.yfinance_collector import fetch_series as fetch_yfinance_series

# KRW 교차환율: base * quote (예: USD/KRW × CNY/USD → CNY/KRW)
DERIVED_KRW_MULTIPLY: dict[str, tuple[str, str]] = {
    'CNY/KRW': ('USD/KRW', 'CNY/USD'),
}


def _align_multiply(
    left: pd.DataFrame,
    right: pd.DataFrame,
) -> pd.DataFrame:
    if left.empty or right.empty:
        return pd.DataFrame()

    merged = left[['Close']].join(right[['Close']], how='inner', lsuffix='_l', rsuffix='_r')
    if merged.empty:
        return pd.DataFrame()

    out = pd.DataFrame({'Close': merged['Close_l'] * merged['Close_r']}, index=merged.index)
    return normalize_ohlcv(out)


def fetch_derived_krw(symbol: str, start: str, end: str) -> pd.DataFrame:
    pair = DERIVED_KRW_MULTIPLY.get(symbol)
    if pair is None:
        return pd.DataFrame()

    left_sym, right_sym = pair
    left = fetch_fdr_series(left_sym, start, end)
    right = fetch_fdr_series(right_sym, start, end)
    return _align_multiply(left, right)


def fetch_fx_series(indicator: dict, start: str, end: str) -> pd.DataFrame:
    source = indicator.get('source', 'fdr')
    symbol = indicator['symbol']

    if source == 'yfinance':
        return fetch_yfinance_series(symbol, start, end)
    if source == 'derived':
        return fetch_derived_krw(symbol, start, end)
    return fetch_fdr_series(symbol, start, end)
