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
        "api_key": os.getenv("DEEPSEEK_API_KEY", "").strip(),
        "model": get_model()
    }


def save_api_key(api_key):
    api_key = api_key.strip()

    if not api_key:
        raise ValueError("API Key 不能为空")

    _update_env_value(
        "DEEPSEEK_API_KEY",
        api_key
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


def get_model():
    load_dotenv(ENV_FILE, override=True)

    return os.getenv(
        "DEEPSEEK_MODEL",
        "deepseek-chat"
    ).strip() or "deepseek-chat"


def clear_api_key():
    _remove_env_value("DEEPSEEK_API_KEY")

    os.environ.pop(
        "DEEPSEEK_API_KEY",
        None
    )


def _update_env_value(name, value):
    lines = _read_env_lines()
    updated = []
    replaced = False

    for line in lines:
        if _is_env_assignment(line, name):
            if not replaced:
                updated.append(f"{name}={value}")
                replaced = True

            continue

        updated.append(line)

    if not replaced:
        updated.append(f"{name}={value}")

    _write_env_lines(updated)


def _remove_env_value(name):
    lines = _read_env_lines()

    if not lines:
        return

    updated = [
        line
        for line in lines
        if not _is_env_assignment(line, name)
    ]

    _write_env_lines(updated)


def _read_env_lines():
    if not ENV_FILE.exists():
        return []

    return ENV_FILE.read_text(
        encoding="utf-8"
    ).splitlines()


def _is_env_assignment(line, name):
    stripped = line.strip()

    if not stripped or stripped.startswith("#"):
        return False

    return (
        stripped.startswith(f"{name}=")
        or stripped.startswith(f"{name} =")
    )


def _write_env_lines(lines):
    ENV_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temp_file = ENV_FILE.with_name(
        ENV_FILE.name + ".tmp"
    )

    content = "\n".join(lines).rstrip()

    temp_file.write_text(
        f"{content}\n" if content else "",
        encoding="utf-8"
    )

    temp_file.replace(ENV_FILE)
