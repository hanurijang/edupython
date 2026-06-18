from __future__ import annotations

import pickle
from datetime import datetime, timedelta
from pathlib import Path

SECTOR_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / 'cache' / 'sector'
SECTOR_TTL = timedelta(days=30)

_memory: dict | None = None


def _cache_path() -> Path:
    return SECTOR_CACHE_DIR / 'kospi.pkl'


def _is_fresh(fetched_at: datetime) -> bool:
    return datetime.now() - fetched_at < SECTOR_TTL


def get_cache_info() -> dict:
    """섹터 캐시 상태를 반환합니다."""
    global _memory

    if _memory is not None and _is_fresh(_memory['fetched_at']):
        fetched_at = _memory['fetched_at']
        return {
            'cached': True,
            'source': 'memory',
            'fetched_at': fetched_at.isoformat(timespec='seconds'),
            'expires_at': (fetched_at + SECTOR_TTL).isoformat(timespec='seconds'),
            'sector_count': len(_memory.get('constituents', {})),
            'mapped_stocks': len(_memory.get('code_to_sector', {})),
        }

    path = _cache_path()
    if not path.exists():
        return {'cached': False, 'source': None}

    with path.open('rb') as f:
        payload = pickle.load(f)

    fetched_at = payload['fetched_at']
    if not _is_fresh(fetched_at):
        return {
            'cached': False,
            'source': 'expired',
            'fetched_at': fetched_at.isoformat(timespec='seconds'),
        }

    return {
        'cached': True,
        'source': 'file',
        'fetched_at': fetched_at.isoformat(timespec='seconds'),
        'expires_at': (fetched_at + SECTOR_TTL).isoformat(timespec='seconds'),
        'sector_count': len(payload.get('constituents', {})),
        'mapped_stocks': len(payload.get('code_to_sector', {})),
    }


def load_sector_cache(*, force_refresh: bool = False) -> dict | None:
    """섹터 캐시를 읽습니다. 없거나 만료되면 None."""
    global _memory

    if force_refresh:
        _memory = None
        return None

    if _memory is not None and _is_fresh(_memory['fetched_at']):
        return _memory

    path = _cache_path()
    if not path.exists():
        return None

    with path.open('rb') as f:
        payload = pickle.load(f)

    if not _is_fresh(payload['fetched_at']):
        return None

    _memory = payload
    return payload


def save_sector_cache(
    constituents: dict[str, list[str]],
    sector_names: dict[str, str],
    code_to_sector: dict[str, str],
) -> dict:
    """섹터 데이터를 메모리·파일 캐시에 저장합니다."""
    global _memory

    SECTOR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now()
    payload = {
        'fetched_at': fetched_at,
        'constituents': constituents,
        'sector_names': sector_names,
        'code_to_sector': code_to_sector,
    }

    with _cache_path().open('wb') as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    for code, stocks in constituents.items():
        _save_sector_item(code, stocks, fetched_at)

    _memory = payload
    return get_cache_info()


def _sector_item_path(code: str) -> Path:
    return SECTOR_CACHE_DIR / 'items' / f'{code}.pkl'


def _save_sector_item(code: str, stocks: list[str], fetched_at: datetime | None = None) -> None:
    fetched_at = fetched_at or datetime.now()
    path = _sector_item_path(code)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as f:
        pickle.dump({'fetched_at': fetched_at, 'stocks': stocks}, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_sector_item(code: str) -> list[str] | None:
    """섹터 단위 캐시를 읽습니다."""
    path = _sector_item_path(code)
    if not path.exists():
        return None
    with path.open('rb') as f:
        payload = pickle.load(f)
    if not _is_fresh(payload['fetched_at']):
        return None
    return list(payload['stocks'])


def assemble_constituents(codes: list[str]) -> dict[str, list[str]] | None:
    """섹터 단위 캐시를 모아 전체 구성종목 dict를 만듭니다."""
    assembled: dict[str, list[str]] = {}
    for code in codes:
        stocks = load_sector_item(code)
        if stocks is None:
            return None
        assembled[code] = stocks
    return assembled
