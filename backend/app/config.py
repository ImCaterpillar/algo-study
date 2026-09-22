import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

load_dotenv(BACKEND_DIR / ".env")


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'algo_study.db'}")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
CREATE_DEMO_USER = _get_bool("CREATE_DEMO_USER", APP_ENV != "production")
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "admin")
DEMO_EMAIL = os.getenv("DEMO_EMAIL", "admin@example.com")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "admin123")

CODE_EXECUTION_ENABLED = _get_bool("CODE_EXECUTION_ENABLED", True)
MAX_CODE_EXECUTION_TIMEOUT = int(os.getenv("MAX_CODE_EXECUTION_TIMEOUT", "10"))
MAX_CODE_EXECUTION_TIMEOUT = max(1, min(MAX_CODE_EXECUTION_TIMEOUT, 30))

_default_cors = "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", _default_cors).split(",") if origin.strip()]

if APP_ENV == "production" and SECRET_KEY == "dev-secret-key-change-me":
    raise RuntimeError("Set a strong SECRET_KEY before running AlgoStudy in production.")
