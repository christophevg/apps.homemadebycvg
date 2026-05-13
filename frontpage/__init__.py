"""
Frontpage application for listing hosted applications.

This module provides the frontpage application that displays all hosted
applications with metadata, links.
"""

import logging
import os
from pathlib import Path

import markdown
import yaml
from quart import Quart, abort, render_template, send_from_directory
from werkzeug.security import safe_join

logger = logging.getLogger(__name__)

FRONTPAGE_LOCAL = os.environ.get("FRONTPAGE_LOCAL", False)

# Load apps configuration
config_file = str(Path.cwd() / "apps.yaml")
try:
  with open(config_file, encoding="utf-8") as fp:
    config : dict[str,dict[str,str]] = yaml.safe_load(fp)
    if not config:
      raise ValueError(f"Empty configuration file: {config}")
  apps = list(config.get("apps", {}).values())
  for app in apps:
    app["description"] = markdown.markdown(app.pop("description", ""))
    if FRONTPAGE_LOCAL and "local" in app:
      app["hostname"] = app["local"]
except KeyError as e:
  raise ValueError(f"Configuration has no apps: {config_file}") from e
except FileNotFoundError as e:
  raise ValueError(f"I need a config file. Tried: {config_file}") from e
except yaml.YAMLError as e:
  raise ValueError(f"Invalid YAML in configuration: {config_file}") from e

# Set up app
FRONTPAGE_FOLDER = Path(__file__).resolve().parent
TEMPLATE_FOLDER  = str(FRONTPAGE_FOLDER / "templates")
STATIC_FOLDER    = str(FRONTPAGE_FOLDER / "static")
HOSTED_FOLDER    = str(FRONTPAGE_FOLDER / "hosted")

app = Quart(
  "frontpage",
  template_folder=TEMPLATE_FOLDER,
  static_folder=STATIC_FOLDER,
  static_url_path=""
)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# wire logging to gunicorn logging if available
logger=logging.getLogger("gunicorn.error")
if logger:
  app.logger.handlers = logger.handlers
  app.logger.setLevel(logger.level)

def ensure_list(str_or_list : list[str] | str) -> list[str]:
  # ensures arg is a list of str ;-)
  if isinstance(str_or_list, list):
    return str_or_list
  return [ str_or_list ]

@app.route("/")
async def show_frontpage():
  """Render frontpage with all hosted applications."""
  return await render_template(
    "index.html",
    apps=apps,
    title=config.get("title", "Apps Homemade by CVG"),
    description=config.get("description", ""),
    ensure_list=ensure_list
  )

@app.route("/hosted/<path:filename>")
async def send_static(filename: str):
  """
  Serve static files from frontpage folder.

  This route serves files from the HOSTED_FOLDER root, used for
  app-specific images configured in YAML.

  Args:
    filename: Path to file relative to HOSTED_FOLDER

  Returns:
    File content with appropriate content-type

  Raises:
    NotFound: If file does not exist or path traversal is attempted
  """
  # Security: Validate path to prevent directory traversal attacks
  safe_path = safe_join(str(HOSTED_FOLDER), filename)
  if safe_path is None:
    # Path traversal attempt detected
    abort(404)
  return await send_from_directory(str(HOSTED_FOLDER), filename)
