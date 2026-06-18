from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from app.config import Config
from app.services.cache import get_cached
from app.services.collectors.base import parse_index_date, period_to_range
from app.services.collectors.fdr_collector import fetch_series as fetch_fdr_series
from app.services.collectors.fx_collector import fetch_fx_series
from app.services.collectors.yfinance_collector import fetch_series as fetch_yfinance_series
from app.services.custom_cards import build_custom_indicators

KR_INDEX_IDS = frozenset({'kospi', 'kosdaq'})

CATEGORIES: list[dict[str, str]] = [
    {'id': 'us_indices', 'label': '미국 지수'},
    {'id': 'kr_market', 'label': '한국 증시'},
    {'id': 'etf_kr', 'label': '한국 ETF'},
    {'id': 'etf_us', 'label': '미국 ETF'},
    {'id': 'bonds', 'label': '채권'},
    {'id': 'fx', 'label': '환율'},
    {'id': 'commodities', 'label': '원자재'},
    {'id': 'crypto', 'label': '코인'},
]

INDICATORS: list[dict[str, Any]] = [
    # US indices
    {'id': 'sp500', 'name': 'S&P 500', 'symbol': 'US500', 'source': 'fdr', 'category': 'us_indices', 'unit': 'pt', 'decimals': 2},
    {'id': 'nasdaq', 'name': '나스닥', 'symbol': 'IXIC', 'source': 'fdr', 'category': 'us_indices', 'unit': 'pt', 'decimals': 2},
    {'id': 'dow', 'name': '다우존스', 'symbol': 'DJI', 'source': 'fdr', 'category': 'us_indices', 'unit': 'pt', 'decimals': 2},
    {'id': 'russell', 'name': '러셀 2000', 'symbol': '^RUT', 'source': 'yfinance', 'category': 'us_indices', 'unit': 'pt', 'decimals': 2},
    {'id': 'vix', 'name': 'VIX', 'symbol': '^VIX', 'source': 'yfinance', 'category': 'us_indices', 'unit': 'pt', 'decimals': 2},
    # KR market — 지수 + 대표 개별종목 (추가 종목은 custom_cards)
    {'id': 'kospi', 'name': '코스피', 'symbol': 'KS11', 'source': 'fdr', 'category': 'kr_market', 'unit': 'pt', 'decimals': 2, 'kr_group': 'index', 'is_default': True},
    {'id': 'kosdaq', 'name': '코스닥', 'symbol': 'KQ11', 'source': 'fdr', 'category': 'kr_market', 'unit': 'pt', 'decimals': 2, 'kr_group': 'index', 'is_default': True},
    {'id': 'samsung', 'name': '삼성전자', 'symbol': '005930', 'source': 'fdr', 'category': 'kr_market', 'unit': 'KRW', 'decimals': 0, 'kr_group': 'stock', 'is_default': True},
    {'id': 'skhynix', 'name': 'SK하이닉스', 'symbol': '000660', 'source': 'fdr', 'category': 'kr_market', 'unit': 'KRW', 'decimals': 0, 'kr_group': 'stock', 'is_default': True},
    # KR ETFs (대표)
    {'id': 'kodex200', 'name': 'KODEX 200', 'symbol': '069500', 'source': 'fdr', 'category': 'etf_kr', 'unit': 'KRW', 'decimals': 0, 'is_default': True},
    {'id': 'tiger_sp500', 'name': 'TIGER 미국S&P500', 'symbol': '360750', 'source': 'fdr', 'category': 'etf_kr', 'unit': 'KRW', 'decimals': 0, 'is_default': True},
    {'id': 'kodex_nasdaq100', 'name': 'KODEX 미국나스닥100TR', 'symbol': '379800', 'source': 'fdr', 'category': 'etf_kr', 'unit': 'KRW', 'decimals': 0, 'is_default': True},
    # US ETFs (대표)
    {'id': 'spy', 'name': 'SPY (S&P500)', 'symbol': 'SPY', 'source': 'yfinance', 'category': 'etf_us', 'unit': 'USD', 'decimals': 2, 'is_default': True},
    {'id': 'qqq', 'name': 'QQQ (나스닥100)', 'symbol': 'QQQ', 'source': 'yfinance', 'category': 'etf_us', 'unit': 'USD', 'decimals': 2, 'is_default': True},
    {'id': 'vti', 'name': 'VTI (미국 전체)', 'symbol': 'VTI', 'source': 'yfinance', 'category': 'etf_us', 'unit': 'USD', 'decimals': 2, 'is_default': True},
    # Bonds (FRED via FDR prefix where available, yfinance fallback)
    {'id': 'us10y', 'name': '미국 10년', 'symbol': 'FRED:DGS10', 'source': 'fdr', 'category': 'bonds', 'unit': '%', 'decimals': 2},
    {'id': 'us2y', 'name': '미국 2년', 'symbol': 'FRED:DGS2', 'source': 'fdr', 'category': 'bonds', 'unit': '%', 'decimals': 2},
    {'id': 'us30y', 'name': '미국 30년', 'symbol': 'FRED:DGS30', 'source': 'fdr', 'category': 'bonds', 'unit': '%', 'decimals': 2},
    {'id': 'fed_funds', 'name': 'Fed Funds', 'symbol': 'FRED:FEDFUNDS', 'source': 'fdr', 'category': 'bonds', 'unit': '%', 'decimals': 2},
    # FX — KRW 직접 환율 중심 (order: 표시 순서, fx_group: krw | reference)
    {'id': 'usdkrw', 'name': 'USD/KRW', 'symbol': 'USD/KRW', 'source': 'fdr', 'category': 'fx', 'fx_group': 'krw', 'order': 1, 'unit': 'KRW', 'decimals': 2},
    {'id': 'eurkrw', 'name': 'EUR/KRW', 'symbol': 'EUR/KRW', 'source': 'fdr', 'category': 'fx', 'fx_group': 'krw', 'order': 2, 'unit': 'KRW', 'decimals': 2},
    {'id': 'jpykrw', 'name': 'JPY/KRW', 'symbol': 'JPY/KRW', 'source': 'fdr', 'category': 'fx', 'fx_group': 'krw', 'order': 3, 'unit': 'KRW', 'decimals': 2},
    {'id': 'gbpkrw', 'name': 'GBP/KRW', 'symbol': 'GBPKRW=X', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'krw', 'order': 4, 'unit': 'KRW', 'decimals': 2},
    {'id': 'cnykrw', 'name': 'CNY/KRW', 'symbol': 'CNY/KRW', 'source': 'derived', 'category': 'fx', 'fx_group': 'krw', 'order': 5, 'unit': 'KRW', 'decimals': 2},
    {'id': 'chfkrw', 'name': 'CHF/KRW', 'symbol': 'CHF/KRW', 'source': 'fdr', 'category': 'fx', 'fx_group': 'krw', 'order': 6, 'unit': 'KRW', 'decimals': 2},
    {'id': 'cadkrw', 'name': 'CAD/KRW', 'symbol': 'CADKRW=X', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'krw', 'order': 7, 'unit': 'KRW', 'decimals': 2},
    {'id': 'audkrw', 'name': 'AUD/KRW', 'symbol': 'AUDKRW=X', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'krw', 'order': 8, 'unit': 'KRW', 'decimals': 2},
    {'id': 'hkdkrw', 'name': 'HKD/KRW', 'symbol': 'HKDKRW=X', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'krw', 'order': 9, 'unit': 'KRW', 'decimals': 2},
    {'id': 'sgdkrw', 'name': 'SGD/KRW', 'symbol': 'SGDKRW=X', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'krw', 'order': 10, 'unit': 'KRW', 'decimals': 2},
    {'id': 'twdkrw', 'name': 'TWD/KRW', 'symbol': 'TWDKRW=X', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'krw', 'order': 11, 'unit': 'KRW', 'decimals': 2},
    {'id': 'thbkrw', 'name': 'THB/KRW', 'symbol': 'THBKRW=X', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'krw', 'order': 12, 'unit': 'KRW', 'decimals': 2},
    {'id': 'nzdkrw', 'name': 'NZD/KRW', 'symbol': 'NZDKRW=X', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'krw', 'order': 13, 'unit': 'KRW', 'decimals': 2},
    {'id': 'inrkrw', 'name': 'INR/KRW', 'symbol': 'INRKRW=X', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'krw', 'order': 14, 'unit': 'KRW', 'decimals': 2},
    {'id': 'zarkrw', 'name': 'ZAR/KRW', 'symbol': 'ZARKRW=X', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'krw', 'order': 15, 'unit': 'KRW', 'decimals': 2},
    {'id': 'dxy', 'name': '달러지수', 'symbol': 'DX-Y.NYB', 'source': 'yfinance', 'category': 'fx', 'fx_group': 'reference', 'order': 101, 'unit': 'pt', 'decimals': 2},
    {'id': 'usdjpy', 'name': 'USD/JPY', 'symbol': 'USD/JPY', 'source': 'fdr', 'category': 'fx', 'fx_group': 'reference', 'order': 102, 'unit': 'JPY', 'decimals': 2},
    {'id': 'eurusd', 'name': 'EUR/USD', 'symbol': 'EUR/USD', 'source': 'fdr', 'category': 'fx', 'fx_group': 'reference', 'order': 103, 'unit': 'USD', 'decimals': 4},
    # Commodities
    {'id': 'gold', 'name': '금', 'symbol': 'GC=F', 'source': 'fdr', 'category': 'commodities', 'unit': 'USD', 'decimals': 2},
    {'id': 'silver', 'name': '은', 'symbol': 'SI=F', 'source': 'fdr', 'category': 'commodities', 'unit': 'USD', 'decimals': 2},
    {'id': 'wti', 'name': 'WTI', 'symbol': 'CL=F', 'source': 'fdr', 'category': 'commodities', 'unit': 'USD', 'decimals': 2},
    {'id': 'brent', 'name': '브렌트', 'symbol': 'BZ=F', 'source': 'fdr', 'category': 'commodities', 'unit': 'USD', 'decimals': 2},
    {'id': 'copper', 'name': '구리', 'symbol': 'HG=F', 'source': 'fdr', 'category': 'commodities', 'unit': 'USD', 'decimals': 2},
    {'id': 'natgas', 'name': '천연가스', 'symbol': 'NG=F', 'source': 'fdr', 'category': 'commodities', 'unit': 'USD', 'decimals': 2},
    # Crypto
    {'id': 'btc', 'name': '비트코인', 'symbol': 'BTC/USD', 'source': 'fdr', 'category': 'crypto', 'unit': 'USD', 'decimals': 0},
    {'id': 'eth', 'name': '이더리움', 'symbol': 'ETH/USD', 'source': 'fdr', 'category': 'crypto', 'unit': 'USD', 'decimals': 0},
]

STATIC_INDICATORS: list[dict[str, Any]] = INDICATORS


def list_default_indicators(category: str | None = None) -> list[dict[str, Any]]:
    items = list(STATIC_INDICATORS)
    if category:
        items = [item for item in items if item['category'] == category]
    return items


def get_indicators(*, force_refresh: bool = False) -> list[dict[str, Any]]:
    custom = build_custom_indicators()
    merged = list(STATIC_INDICATORS) + custom
    return merged


def _indicator_index(force_refresh: bool = False) -> dict[str, dict[str, Any]]:
    return {item['id']: item for item in get_indicators(force_refresh=force_refresh)}


def get_categories() -> list[dict[str, str]]:
    return list(CATEGORIES)


def get_indicator(indicator_id: str) -> dict[str, Any] | None:
    return _indicator_index().get(indicator_id)


def list_indicators(category: str | None = None) -> list[dict[str, Any]]:
    items = get_indicators()
    if category:
        items = [item for item in items if item['category'] == category]
        if category == 'fx':
            return sorted(items, key=lambda item: item.get('order', 999))
        if category == 'kr_market':
            return sorted(
                items,
                key=lambda item: (
                    0 if item['id'] in KR_INDEX_IDS else 1,
                    0 if item.get('is_default') else 1,
                    item.get('name', ''),
                ),
            )
        if category in ('etf_kr', 'etf_us'):
            return sorted(items, key=lambda item: (0 if item.get('is_default') else 1, item.get('name', '')))
        return items
    return items


def _round_num(value: float, decimals: int = 2) -> float:
    return round(float(value), decimals)


def _direction(change: float) -> str:
    if change > 0:
        return 'up'
    if change < 0:
        return 'down'
    return 'flat'


def _fetch_df(indicator: dict[str, Any], start: str, end: str) -> pd.DataFrame:
    if indicator.get('category') == 'fx':
        return fetch_fx_series(indicator, start, end)
    symbol = indicator['symbol']
    if indicator['source'] == 'yfinance':
        return fetch_yfinance_series(symbol, start, end)
    return fetch_fdr_series(symbol, start, end)


def _snapshot_from_df(indicator: dict[str, Any], df: pd.DataFrame) -> dict[str, Any] | None:
    if df.empty:
        return None

    row = df.iloc[-1]
    close = float(row['Close'])
    if len(df) > 1:
        prev_close = float(df.iloc[-2]['Close'])
        change = close - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0
    else:
        change = 0.0
        change_pct = 0.0

    decimals = indicator.get('decimals', 2)
    return {
        'id': indicator['id'],
        'name': indicator['name'],
        'symbol': indicator['symbol'],
        'category': indicator['category'],
        'unit': indicator.get('unit', ''),
        'fx_group': indicator.get('fx_group'),
        'decimals': decimals,
        'close': _round_num(close, decimals),
        'change': _round_num(change, decimals),
        'change_pct': _round_num(change_pct, 2),
        'direction': _direction(change),
        'date': parse_index_date(df.index[-1]),
        'is_default': indicator.get('is_default', False),
        'is_custom': indicator.get('is_custom', False),
    }


def _load_snapshot(indicator: dict[str, Any]) -> dict[str, Any] | None:
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    df = _fetch_df(indicator, start, end)
    snap = _snapshot_from_df(indicator, df)
    if snap is None:
        return {
            'id': indicator['id'],
            'name': indicator['name'],
            'symbol': indicator['symbol'],
            'category': indicator['category'],
            'unit': indicator.get('unit', ''),
            'fx_group': indicator.get('fx_group'),
            'decimals': indicator.get('decimals', 2),
            'close': None,
            'change': None,
            'change_pct': None,
            'direction': 'flat',
            'date': None,
            'error': '데이터를 불러올 수 없습니다.',
            'is_default': indicator.get('is_default', False),
            'is_custom': indicator.get('is_custom', False),
        }
    return snap


def get_indicator_snapshot(indicator_id: str, *, force_refresh: bool = False) -> dict[str, Any] | None:
    indicator = get_indicator(indicator_id)
    if indicator is None:
        return None

    ttl = 0 if force_refresh else Config.SNAPSHOT_TTL_SEC
    key = f"snapshot:{indicator_id}"
    if ttl == 0:
        return _load_snapshot(indicator)
    return get_cached(key, ttl, lambda: _load_snapshot(indicator))


def get_snapshots(category: str, *, force_refresh: bool = False) -> list[dict[str, Any]]:
    indicators = list_indicators(category)
    ttl = 0 if force_refresh else Config.SNAPSHOT_TTL_SEC
    results: list[dict[str, Any]] = []
    for indicator in indicators:
        key = f"snapshot:{indicator['id']}"
        if ttl == 0:
            snap = _load_snapshot(indicator)
        else:
            snap = get_cached(key, ttl, lambda ind=indicator: _load_snapshot(ind))
        if snap:
            results.append(snap)
    return results


def get_series(indicator_id: str, period: str = '1y', *, force_refresh: bool = False) -> dict[str, Any]:
    indicator = get_indicator(indicator_id)
    if indicator is None:
        raise KeyError(indicator_id)

    start, end = period_to_range(period)
    ttl = 0 if force_refresh else Config.SERIES_TTL_SEC
    key = f"series:{indicator_id}:{period}"

    def loader() -> pd.DataFrame:
        return _fetch_df(indicator, start, end)

    df = loader() if ttl == 0 else get_cached(key, ttl, loader)
    if df.empty:
        return {
            'id': indicator_id,
            'name': indicator['name'],
            'period': period,
            'points': [],
        }

    points = [
        {'date': parse_index_date(idx), 'close': _round_num(row['Close'], indicator.get('decimals', 2))}
        for idx, row in df.iterrows()
    ]
    return {
        'id': indicator_id,
        'name': indicator['name'],
        'symbol': indicator['symbol'],
        'unit': indicator.get('unit', ''),
        'period': period,
        'points': points,
    }
