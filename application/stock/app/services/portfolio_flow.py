from __future__ import annotations

from datetime import datetime, timedelta

import FinanceDataReader as fdr
import pandas as pd

BENCHMARKS = [
    {'name': '코스피', 'market': 'KRX', 'symbol': 'KS11'},
    {'name': '나스닥', 'market': 'NASDAQ', 'symbol': 'IXIC'},
    {'name': 'S&P500', 'market': 'S&P500', 'symbol': 'US500'},
]


def _reader_symbol(market: str, symbol: str) -> str:
    if market in ('KRX', 'ETF/KR', 'S&P500'):
        return symbol
    return f'{market}:{symbol}'


def _normalize_weights(holdings: list[dict]) -> list[float]:
    raw = [max(0.0, float(item.get('weight', 0) or 0)) for item in holdings]
    total = sum(raw)
    if total <= 0:
        n = len(holdings)
        return [1.0 / n for _ in holdings] if n else []
    return [w / total for w in raw]


def _fetch_close_series(market: str, symbol: str, start: str, end: str) -> pd.Series | None:
    candidates = [_reader_symbol(market, symbol)]
    if symbol not in candidates:
        candidates.append(symbol)
    if market == 'NASDAQ' and '^IXIC' not in candidates and symbol == 'IXIC':
        candidates.append('^IXIC')

    df = None
    for candidate in candidates:
        try:
            df = fdr.DataReader(candidate, start, end)
            if df is not None and not df.empty:
                break
        except Exception:
            df = None
            continue
    if df is None:
        return None
    if df.empty:
        return None

    col = 'Close' if 'Close' in df.columns else 'Adj Close' if 'Adj Close' in df.columns else None
    if col is None:
        return None

    series = pd.to_numeric(df[col], errors='coerce').dropna()
    if series.empty:
        return None
    series.index = pd.to_datetime(series.index).strftime('%Y-%m-%d')
    return series


def get_portfolio_flow(holdings: list[dict], *, days: int = 0) -> dict:
    """포트폴리오 내 종목의 기준가(1) 수익 흐름을 반환합니다."""
    if not holdings:
        return {'dates': [], 'series': [], 'portfolio': []}

    end_dt = datetime.now()
    if days and days > 0:
        start_dt = end_dt - timedelta(days=max(7, days))
        start = start_dt.strftime('%Y-%m-%d')
    else:
        # 가능한 한 긴 기간을 조회 (시장/종목 상장 이력 범위 내)
        start = '1990-01-01'
    end = end_dt.strftime('%Y-%m-%d')

    raw_series: list[tuple[dict, pd.Series]] = []
    for item in holdings:
        market = str(item.get('market', '')).strip()
        symbol = str(item.get('symbol', '')).strip()
        if not market or not symbol:
            continue
        series = _fetch_close_series(market, symbol, start, end)
        if series is None or series.empty:
            continue
        raw_series.append((item, series))

    if not raw_series:
        return {'dates': [], 'series': [], 'portfolio': []}

    common_index = set(raw_series[0][1].index.tolist())
    for _, series in raw_series[1:]:
        common_index &= set(series.index.tolist())

    if not common_index:
        return {'dates': [], 'series': [], 'portfolio': []}

    dates = sorted(common_index)
    aligned_series: list[dict] = []
    weight_source: list[dict] = []
    for item, series in raw_series:
        values = [round(float(series.loc[d]), 6) for d in dates]
        aligned_series.append({
            'name': item.get('name') or item.get('symbol'),
            'symbol': item.get('symbol'),
            'market': item.get('market'),
            'values': values,
        })
        weight_source.append(item)

    weights = _normalize_weights(weight_source)
    for sidx, series in enumerate(aligned_series):
        series['weight'] = round(float(weights[sidx]), 6)

    benchmark_series: list[dict] = []
    date_index = pd.to_datetime(dates)
    for benchmark in BENCHMARKS:
        raw = _fetch_close_series(benchmark['market'], benchmark['symbol'], start, end)
        if raw is None or raw.empty:
            continue

        raw_dt = raw.copy()
        raw_dt.index = pd.to_datetime(raw_dt.index)
        aligned = raw_dt.reindex(date_index, method='ffill').bfill()
        if aligned.isna().all():
            continue

        values = [round(float(v), 6) for v in aligned.tolist()]
        benchmark_series.append({
            'name': benchmark['name'],
            'symbol': benchmark['symbol'],
            'market': benchmark['market'],
            'values': values,
        })

    return {
        'dates': dates,
        'series': aligned_series,
        'benchmarks': benchmark_series,
        'start_date': dates[0],
        'end_date': dates[-1],
        'default_base_date': dates[-1],
    }
