import json
import logging
from pathlib import Path
from sys import platform

from pydantic import BaseModel, BaseSettings, validator

_LOGGER = logging.getLogger(__name__)


class _FileSettings:
    """App configuration"""

    ease_config_folder: Path = (Path.home()).joinpath(".ease")
    temp_installation_folder: Path = (Path.home()).joinpath(".ease", "bin")

    def __init__(self):
        self.ease_config_folder.mkdir(exist_ok=True)
        self.temp_installation_folder.mkdir(exist_ok=True)

    @property
    def config_file(self):
        return self.ease_config_folder.joinpath("fab-deploy.json")

    @property
    def version_file(self):
        return self.temp_installation_folder.joinpath("version.json")


_file_settings = None


def get_file_settings() -> _FileSettings:
    """Get one instance of the config"""
    global _file_settings
    if _file_settings is None:
        _file_settings = _FileSettings()

    return _file_settings


class _Settings(BaseSettings):
    """Fab deploy settings.

    download_url: # URL base folder where binaries and version info is stored.
    """

    download_url: str = None
    installation_folder: Path = Path.home() / "fabricator"
    key: str = None

    @validator("download_url", pre=True, always=True)
    def platform_default(cls, v, values, **kwargs):
        """Set download url depending on platform."""
        if v is None:
            if platform == "linux":
                return "https://motorisation.hde.nl/bin/fabricator/ubuntu18_04/"
            elif platform == "win32":
                return "https://motorisation.hde.nl/bin/fabricator/win10/"
        else:
            return v


def save_settings(settings: _Settings, settings_file: Path):
    """Save app settings."""
    with open(settings_file, "w") as fl:
        fl.write(settings.json())


def load_settings(settings_file: Path) -> _Settings:
    """Load app settings"""

    if not settings_file.exists():
        settings = _Settings()
    else:
        with open(settings_file) as fl:
            dct = json.load(fl)
        settings = _Settings(**dct)

    settings.installation_folder.mkdir(exist_ok=True, parents=True)
    return settings


INFO_COLOR = "cyan"
OK_COLOR = "green"
ERROR_COLOR = "bright_red"

KEY_WINDOWS = "win32"
KEY_LINUX = "linux"

KEY_PLATFORM = platform
