from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

PERIOD_DAYS = {
    '1m': 31,
    '3m': 93,
    '6m': 186,
    '1y': 366,
    '3y': 366 * 3,
    '5y': 366 * 5,
}


def period_to_range(period: str) -> tuple[str, str]:
    days = PERIOD_DAYS.get(period, PERIOD_DAYS['1y'])
    end = datetime.now()
    start = end - timedelta(days=days)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    out = out.sort_index()
    if 'Close' not in out.columns:
        for col in ('Adj Close', 'close', 'price'):
            if col in out.columns:
                out = out.rename(columns={col: 'Close'})
                break
        else:
            # FRED 등 단일 값 시계열은 Close 대신 시리즈 ID 컬럼명 사용
            value_cols = [
                col for col in out.columns
                if str(col).lower() not in ('open', 'high', 'low', 'volume')
            ]
            if len(value_cols) == 1:
                out = out.rename(columns={value_cols[0]: 'Close'})
            elif value_cols:
                out = out.rename(columns={value_cols[0]: 'Close'})

    return out.dropna(subset=['Close']) if 'Close' in out.columns else pd.DataFrame()


def parse_index_date(value) -> str:
    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d')
    return str(value)[:10]
