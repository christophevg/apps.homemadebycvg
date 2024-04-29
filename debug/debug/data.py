import os
import logging

logger = logging.getLogger(__name__)

os.environ._debug = True
DB_CONN = os.environ.get("MONGODB_URI", "default")
os.environ._debug = False

logger.info(f"DB_CONN={DB_CONN}")

from debug import server

@server.route("/")
def handle():
  fresh = os.environ.get("MONGODB_URI", "default")
  return f"{DB_CONN} / {fresh}"
