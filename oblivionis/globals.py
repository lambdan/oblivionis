import logging
import os

DEBUG = os.environ.get("DEBUG") == "1"

if DEBUG:
    print("⚠️⚠️⚠️ Running in DEBUG mode ⚠️⚠️⚠️")

ADMINS = os.environ.get("ADMINS", "").split(",") if os.environ.get("ADMINS") else []

LOGLEVEL = logging.DEBUG if DEBUG else logging.INFO

logging.basicConfig(level=LOGLEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")