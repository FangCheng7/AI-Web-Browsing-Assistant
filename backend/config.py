import os
from pathlib import Path
from dotenv import load_dotenv

APP_NAME = "AI网页浏览分析助手"

DATA_DIR = Path.home() / "AppData" / "Local" / APP_NAME
DATA_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = DATA_DIR / ".env"

# 开发环境仍然支持 backend/.env
DEV_ENV_FILE = Path(__file__).resolve().parent / ".env"

if DEV_ENV_FILE.exists():
    load_dotenv(DEV_ENV_FILE, override=False)

if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)


def load_config():
    load_dotenv(ENV_FILE, override=True)

    return {
        "provider": "DeepSeek",
        "api_key": os.getenv("DEEPSEEK_API_KEY", "").strip()
    }


def save_api_key(api_key):
    api_key = api_key.strip()

    if not api_key:
        raise ValueError("API Key 不能为空")

    ENV_FILE.write_text(
        f"DEEPSEEK_API_KEY={api_key}\n",
        encoding="utf-8"
    )

    os.environ["DEEPSEEK_API_KEY"] = api_key


def get_api_key():
    load_dotenv(ENV_FILE, override=True)

    return os.getenv(
        "DEEPSEEK_API_KEY",
        ""
    ).strip()


def has_api_key():
    return bool(get_api_key())


def clear_api_key():
    if ENV_FILE.exists():
        ENV_FILE.unlink()

    os.environ.pop(
        "DEEPSEEK_API_KEY",
        None
    )