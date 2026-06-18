from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import Config

CUSTOMIZABLE_CATEGORIES = frozenset({'kr_market', 'etf_kr', 'etf_us'})

CUSTOM_CARDS_DIR = Config.DATA_DIR / 'custom_cards'

_US_TICKER = re.compile(r'^[A-Z][A-Z0-9.\-]{0,9}$')


def _ensure_dir() -> None:
    CUSTOM_CARDS_DIR.mkdir(parents=True, exist_ok=True)


def _category_file(category: str) -> Path:
    return CUSTOM_CARDS_DIR / f'{category}.json'


def _default_payload() -> dict[str, Any]:
    return {'updated_at': None, 'items': []}


def _load_payload(category: str) -> dict[str, Any]:
    if category not in CUSTOMIZABLE_CATEGORIES:
        return _default_payload()

    _ensure_dir()
    path = _category_file(category)
    if not path.exists():
        return _default_payload()

    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return _default_payload()

    items = data.get('items', [])
    if not isinstance(items, list):
        items = []
    return {'updated_at': data.get('updated_at'), 'items': items}


def _save_payload(category: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    _ensure_dir()
    payload = {
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'items': items,
    }
    _category_file(category).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    return payload


def make_custom_id(category: str, symbol: str) -> str:
    symbol = symbol.strip()
    if category == 'kr_market':
        return f'custom_kr_{symbol.zfill(6)}'
    if category == 'etf_kr':
        return f'custom_etf_kr_{symbol.zfill(6)}'
    return f'custom_etf_us_{symbol.upper()}'


def build_indicator(entry: dict[str, Any]) -> dict[str, Any]:
    category = entry['category']
    unit = 'USD' if category == 'etf_us' else 'KRW'
    decimals = 2 if category == 'etf_us' else 0
    source = entry.get('source') or ('yfinance' if category == 'etf_us' else 'fdr')
    return {
        'id': entry['id'],
        'name': entry['name'],
        'symbol': entry['symbol'],
        'source': source,
        'category': category,
        'unit': unit,
        'decimals': decimals,
        'is_custom': True,
    }


def load_custom_entries(category: str | None = None) -> list[dict[str, Any]]:
    if category:
        return list(_load_payload(category).get('items', []))

    entries: list[dict[str, Any]] = []
    for cat in CUSTOMIZABLE_CATEGORIES:
        entries.extend(_load_payload(cat).get('items', []))
    return entries


def build_custom_indicators(category: str | None = None) -> list[dict[str, Any]]:
    return [build_indicator(entry) for entry in load_custom_entries(category)]


def load_custom_ids(category: str) -> list[str]:
    return [str(item['id']) for item in load_custom_entries(category) if item.get('id')]


def get_revision_token() -> str:
    parts: list[str] = []
    for category in sorted(CUSTOMIZABLE_CATEGORIES):
        payload = _load_payload(category)
        parts.append(f"{category}:{payload.get('updated_at') or 'empty'}:{len(payload.get('items', []))}")
    return '|'.join(parts)


def _normalize_symbol(category: str, symbol: str) -> str:
    symbol = symbol.strip()
    if category in ('kr_market', 'etf_kr'):
        return symbol.zfill(6)
    return symbol.upper()


def add_custom_card(category: str, *, symbol: str, name: str) -> dict[str, Any]:
    if category not in CUSTOMIZABLE_CATEGORIES:
        raise ValueError('unsupported category')

    symbol = _normalize_symbol(category, symbol)
    name = name.strip()
    if not symbol or not name:
        raise ValueError('symbol and name required')

    from app.services.indicators import list_default_indicators

    for item in list_default_indicators(category):
        if item['symbol'] == symbol:
            raise ValueError('이미 기본 카드에 포함된 항목입니다.')

    payload = _load_payload(category)
    items: list[dict[str, Any]] = list(payload.get('items', []))
    custom_id = make_custom_id(category, symbol)
    if any(item.get('id') == custom_id or item.get('symbol') == symbol for item in items):
        raise ValueError('이미 추가된 카드입니다.')

    entry = {
        'id': custom_id,
        'category': category,
        'symbol': symbol,
        'name': name,
        'source': 'yfinance' if category == 'etf_us' else 'fdr',
    }
    items.append(entry)
    saved = _save_payload(category, items)
    return {'entry': entry, 'payload': saved}


def remove_custom_card(category: str, indicator_id: str) -> dict[str, Any]:
    if category not in CUSTOMIZABLE_CATEGORIES:
        raise ValueError('unsupported category')

    payload = _load_payload(category)
    items = [item for item in payload.get('items', []) if item.get('id') != indicator_id]
    saved = _save_payload(category, items)
    return {'removed': indicator_id, 'payload': saved}


def is_custom_indicator(indicator_id: str) -> bool:
    return indicator_id.startswith('custom_')


def validate_us_etf_ticker(symbol: str) -> tuple[str, str] | None:
    ticker = symbol.strip().upper()
    if not _US_TICKER.match(ticker):
        return None
    try:
        from app.services.collectors.yfinance_collector import fetch_series
        from datetime import timedelta

        end = datetime.now().strftime('%Y-%m-%d')
        start = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        df = fetch_series(ticker, start, end)
        if df.empty:
            return None
        return ticker, ticker
    except Exception:
        return None
