"""Run from this repository with python main.py."""
import logging
import os

import uvicorn
from routes import CONFIG
from service import create_app

app = create_app(CONFIG)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    uvicorn.run(app, host=os.environ.get("LISTEN_ADDR", "127.0.0.1"),
                port=int(os.environ.get("PORT", CONFIG.port)), access_log=False)
