import os
import logging

logger = logging.getLogger(__name__)

DB_CONN = os.environ.get("MONGODB_URI", "default")

logger.info(f"DB_CONN={DB_CONN}")

logger.info(type(os.environ))

for k, v in os.environ.items():
  logger.info(f"DEBUG: {k} = {v}")

from debug import server

@server.route("/")
def handle():
  fresh = os.environ.get("MONGODB_URI", "default")
  return f"{DB_CONN} / {fresh}"
