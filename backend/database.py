from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

APP_NAME = "AI网页浏览分析助手"

# 用户本地数据目录
DATA_DIR = Path.home() / "AppData" / "Local" / APP_NAME
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_FILE = DATA_DIR / "browser.db"

DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def ensure_schema():
    """Add columns introduced after the first release."""

    inspector = inspect(engine)

    if "page_analyses" not in inspector.get_table_names():
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("page_analyses")
    }

    with engine.begin() as connection:
        if "tags" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE page_analyses "
                    "ADD COLUMN tags TEXT"
                )
            )

        if "analysis_source" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE page_analyses "
                    "ADD COLUMN analysis_source VARCHAR(20)"
                )
            )
