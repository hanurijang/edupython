import pickle
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / 'cache' / 'listings'
LISTING_TTL = timedelta(days=7)

CACHED_MARKETS = frozenset([
    'KRX',
    'NASDAQ', 'NYSE', 'AMEX', 'S&P500',
    'SSE', 'SZSE', 'HKEX', 'TSE', 'HOSE',
])

_memory: dict[str, dict] = {}


def is_cached_market(market: str) -> bool:
    return market in CACHED_MARKETS


def _cache_path(market: str) -> Path:
    safe = market.replace('/', '_').replace('&', 'and')
    return CACHE_DIR / f'{safe}.pkl'


def _is_fresh(fetched_at: datetime) -> bool:
    return datetime.now() - fetched_at < LISTING_TTL


def get_cache_info(market: str) -> dict | None:
    if not is_cached_market(market):
        return None

    if market in _memory and _is_fresh(_memory[market]['fetched_at']):
        fetched_at = _memory[market]['fetched_at']
        return {
            'cached': True,
            'source': 'memory',
            'fetched_at': fetched_at.isoformat(timespec='seconds'),
            'expires_at': (fetched_at + LISTING_TTL).isoformat(timespec='seconds'),
            'count': len(_memory[market]['df']),
        }

    path = _cache_path(market)
    if not path.exists():
        return {'cached': False, 'source': None}

    with path.open('rb') as f:
        payload = pickle.load(f)

    fetched_at = payload['fetched_at']
    if not _is_fresh(fetched_at):
        return {'cached': False, 'source': 'expired', 'fetched_at': fetched_at.isoformat(timespec='seconds')}

    return {
        'cached': True,
        'source': 'file',
        'fetched_at': fetched_at.isoformat(timespec='seconds'),
        'expires_at': (fetched_at + LISTING_TTL).isoformat(timespec='seconds'),
        'count': len(payload['df']),
    }


def load_listing(market: str, *, force_refresh: bool = False) -> tuple[pd.DataFrame | None, dict | None]:
    """캐시에서 종목 목록을 읽습니다. 없거나 만료되면 (None, info)를 반환합니다."""
    if not is_cached_market(market):
        return None, None

    if force_refresh:
        _memory.pop(market, None)
        return None, get_cache_info(market)

    if market in _memory:
        payload = _memory[market]
        if _is_fresh(payload['fetched_at']):
            return payload['df'].copy(), get_cache_info(market)

    path = _cache_path(market)
    if not path.exists():
        return None, get_cache_info(market)

    with path.open('rb') as f:
        payload = pickle.load(f)

    if not _is_fresh(payload['fetched_at']):
        return None, get_cache_info(market)

    df = payload['df']
    _memory[market] = {'fetched_at': payload['fetched_at'], 'df': df}
    return df.copy(), get_cache_info(market)


def save_listing(market: str, df: pd.DataFrame) -> dict:
    """종목 목록을 파일·메모리 캐시에 저장합니다."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now()
    payload = {'fetched_at': fetched_at, 'df': df}

    with _cache_path(market).open('wb') as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    _memory[market] = payload
    return get_cache_info(market) or {}
