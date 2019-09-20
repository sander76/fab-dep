import logging
import shutil
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

deploy_folder = Path("/app/fab/usr/bin/")
config_folder = Path("/app/fab/")

version = __version

shutil.rmtree()