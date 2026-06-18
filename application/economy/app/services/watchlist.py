from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import Config

FAVORITES_FILE = Config.FAVORITES_DIR / 'watchlist.json'


def _ensure_dir() -> None:
    Config.FAVORITES_DIR.mkdir(parents=True, exist_ok=True)


def _default_payload() -> dict:
    return {'updated_at': None, 'items': []}


def load_favorites() -> list[str]:
    _ensure_dir()
    if not FAVORITES_FILE.exists():
        return []

    try:
        data = json.loads(FAVORITES_FILE.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return []

    items = data.get('items', [])
    ids: list[str] = []
    for item in items:
        if isinstance(item, str):
            ids.append(item)
        elif isinstance(item, dict) and item.get('id'):
            ids.append(str(item['id']))
    return ids


def save_favorites(ids: list[str]) -> dict:
    _ensure_dir()
    unique_ids: list[str] = []
    seen: set[str] = set()
    for indicator_id in ids:
        if indicator_id and indicator_id not in seen:
            unique_ids.append(indicator_id)
            seen.add(indicator_id)

    payload = {
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'items': [{'id': indicator_id} for indicator_id in unique_ids],
    }
    FAVORITES_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    return payload


def add_favorite(indicator_id: str) -> list[str]:
    ids = load_favorites()
    if indicator_id not in ids:
        ids.append(indicator_id)
    save_favorites(ids)
    return load_favorites()


def remove_favorite(indicator_id: str) -> list[str]:
    ids = [item for item in load_favorites() if item != indicator_id]
    save_favorites(ids)
    return ids


def is_favorite(indicator_id: str) -> bool:
    return indicator_id in load_favorites()


def get_favorite_snapshots(*, force_refresh: bool = False) -> list[dict[str, Any]]:
    from app.services.indicators import get_indicator_snapshot

    cards: list[dict[str, Any]] = []
    for indicator_id in load_favorites():
        snap = get_indicator_snapshot(indicator_id, force_refresh=force_refresh)
        if snap:
            cards.append(snap)
    return cards
