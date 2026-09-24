import sys
import threading
import time
from pathlib import Path

import uvicorn
import webview


if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent


BACKEND_DIR = BASE_DIR / "backend"


def start_backend():
    sys.path.insert(0, str(BACKEND_DIR))

    from main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )


def main():
    print("=" * 50)
    print("AI网页浏览分析助手")
    print("=" * 50)
    print("正在启动后端服务...")

    backend_thread = threading.Thread(
        target=start_backend,
        daemon=True
    )

    backend_thread.start()

    time.sleep(3)

    print("后端启动完成")

    window = webview.create_window(
        "AI网页浏览分析助手",
        "http://127.0.0.1:8000/dashboard/",
        width=1400,
        height=900,
        min_size=(1100, 700),
        resizable=True,
        text_select=True
    )

    webview.start(debug=False)


if __name__ == "__main__":
    main()