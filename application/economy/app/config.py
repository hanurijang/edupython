from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    CACHE_DIR = BASE_DIR / 'cache'
    DATA_DIR = BASE_DIR / 'data'
    FAVORITES_DIR = BASE_DIR / 'data' / 'favorites'
    CUSTOM_CARDS_DIR = BASE_DIR / 'data' / 'custom_cards'
    DEFAULT_CATEGORY = 'fx'
    SNAPSHOT_TTL_SEC = 300
    SERIES_TTL_SEC = 900
