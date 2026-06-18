"""edupython 프로젝트 루트의 .env 로드."""

from pathlib import Path

EDUPYTHON_ROOT = Path(__file__).resolve().parent
ENV_PATH = EDUPYTHON_ROOT / '.env'


def load_edupython_env() -> bool:
    """edupython/.env 를 로드합니다. python-dotenv 미설치 시 False."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False
    return load_dotenv(ENV_PATH)
