import logging
import os

DEBUG = os.environ.get("DEBUG") == "1"

LOGLEVEL = logging.DEBUG if DEBUG else logging.INFO

logging.basicConfig(level=LOGLEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")