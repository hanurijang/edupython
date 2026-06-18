import sys
from pathlib import Path

from flask import Flask

from app.routes import bp

BASE_DIR = Path(__file__).resolve().parent.parent
EDUPYTHON_ROOT = BASE_DIR.parent.parent

if str(EDUPYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(EDUPYTHON_ROOT))

from env_loader import load_edupython_env  # noqa: E402

load_edupython_env()


def create_app():
    app = Flask(__name__, template_folder=str(BASE_DIR / 'templates'))
    app.config.from_object('app.config.Config')
    app.register_blueprint(bp)
    return app
