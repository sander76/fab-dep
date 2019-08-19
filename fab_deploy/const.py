import logging
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

EASE_CONFIG_FOLDER = (Path.home()).joinpath(".ease")
INSTALLATION_FOLDER = (Path.home()).joinpath("fabricator")
FAB_DEPLOY_CONFIG = EASE_CONFIG_FOLDER.joinpath("fab-deploy.json")
TEMP_FOLDER = (Path.home()).joinpath(".ease", "bin")
VERSION_FILE = TEMP_FOLDER.joinpath("version.json")
LOGGER = logging.getLogger("__name__")
INFO_COLOR = "cyan"
OK_COLOR = "green"
ERROR_COLOR = "red"