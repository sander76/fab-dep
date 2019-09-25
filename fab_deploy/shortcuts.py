import logging
import shutil
import subprocess
from pathlib import Path
from sys import platform
from typing import List, Optional

import click

from fab_deploy.const import ERROR_COLOR

_LOGGER = logging.getLogger(__name__)


def copy_shortcuts(installation_folder: Path):
    """Copy desktop shortcuts"""
    desktop = Path.home() / "Desktop"

    if platform == "linux":
        shortcut_folder = installation_folder / "resources" / "linux" / "shortcuts"
        files = _copy_files(desktop, shortcut_folder)

        for file in files:
            _make_executable(file)

    elif platform == "win32":
        shortcut_folder = installation_folder / "resources" / "win10" / "shortcuts"
        _copy_files(desktop, shortcut_folder)


def _make_executable(file: Path):
    subprocess.run(["chmod", "+x", str(file)])


def _copy_files(desktop: Path, shortcut_folder: Path) -> Optional[List[Path]]:
    if shortcut_folder.exists():
        files = []
        for file in shortcut_folder.glob("*.*"):
            shutil.copy(file, desktop / file.name)
            files.append(desktop / file.name)
        return files
    else:
        click.secho("Shortcut folder does not exist.", bg=ERROR_COLOR)
