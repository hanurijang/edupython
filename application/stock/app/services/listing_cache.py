import pickle
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / 'cache' / 'listings'
# 네이버 실시간 갱신 결과만 보관 (다음 실시간 갱신까지 유지)
NAVER_LISTING_MAX_AGE = timedelta(days=1)

_memory: dict[str, dict] = {}


def _cache_path(market: str) -> Path:
    safe = market.replace('/', '_').replace('&', 'and')
    return CACHE_DIR / f'{safe}.pkl'


def _read_payload(market: str) -> dict | None:
    if market in _memory:
        return _memory[market]

    path = _cache_path(market)
    if not path.exists():
        return None

    with path.open('rb') as f:
        payload = pickle.load(f)

    _memory[market] = payload
    return payload


def load_naver_listing(market: str) -> pd.DataFrame | None:
    """저장된 네이버 실시간 목록을 반환합니다 (없거나 만료 시 None)."""
    payload = _read_payload(market)
    if payload is None or payload.get('data_source') != 'naver':
        return None
    if datetime.now() - payload['fetched_at'] > NAVER_LISTING_MAX_AGE:
        return None
    return payload['df'].copy()


def save_naver_listing(market: str, df: pd.DataFrame) -> dict:
    """네이버 실시간 조회 결과만 저장합니다."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now()
    payload = {
        'fetched_at': fetched_at,
        'df': df,
        'data_source': 'naver',
    }

    with _cache_path(market).open('wb') as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    _memory[market] = payload
    return get_listing_meta(market) or {}


def get_listing_meta(market: str) -> dict | None:
    payload = _read_payload(market)
    if payload is None or payload.get('data_source') != 'naver':
        return {'cached': False, 'data_source': 'fdr', 'storage': None}

    fetched_at = payload['fetched_at']
    if datetime.now() - fetched_at > NAVER_LISTING_MAX_AGE:
        return {
            'cached': False,
            'data_source': 'naver',
            'storage': 'expired',
            'fetched_at': fetched_at.isoformat(timespec='seconds'),
        }

    return {
        'cached': True,
        'data_source': 'naver',
        'storage': 'memory' if market in _memory else 'file',
        'fetched_at': fetched_at.isoformat(timespec='seconds'),
        'count': len(payload['df']),
    }
