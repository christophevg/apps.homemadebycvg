import logging
import os

from flask import Flask

# setup logging to stdout
LOG_LEVEL = os.environ.get("LOG_LEVEL") or "DEBUG"
FORMAT    = "[%(name)s] [%(levelname)s] %(message)s"
DATEFMT   = "%Y-%m-%d %H:%M:%S %z"

logging.basicConfig(level=LOG_LEVEL, format=FORMAT, datefmt=DATEFMT)
formatter = logging.Formatter(FORMAT, DATEFMT)
logging.getLogger().handlers[0].setFormatter(formatter)

logger = logging.getLogger(__name__)

for k, v in os.environ.items():
  logger.info(f"HELLO: {k} = {v}")

# create app
app = Flask(__name__)

@app.route("/")
def hello_world():
  return "👋 Hello!"
