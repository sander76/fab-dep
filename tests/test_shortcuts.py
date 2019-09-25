import logging
from pathlib import Path
from unittest.mock import Mock

from fab_deploy.shortcuts import copy_shortcuts, _copy_files

_LOGGER = logging.getLogger(__name__)


def test_copy_shortcuts_linux(monkeypatch):
    monkeypatch.setattr("fab_deploy.shortcuts.platform", "linux")

    mock_copy = Mock()
    monkeypatch.setattr("fab_deploy.shortcuts._copy_files", mock_copy)

    install_base_folder = Path("temp")
    short_cuts_folder = install_base_folder / "resources" / "linux" / "shortcuts"

    copy_shortcuts(install_base_folder)

    assert mock_copy.called_with(Path.home() / "Desktop", short_cuts_folder)


def test_copy_short_cuts_linux(monkeypatch):
    monkeypatch.setattr("fab_deploy.shortcuts.platform", "win32")

    mock_copy = Mock()
    monkeypatch.setattr("fab_deploy.shortcuts._copy_files", mock_copy)

    install_base_folder = Path("temp")
    short_cuts_folder = install_base_folder / "resources" / "win10" / "shortcuts"

    copy_shortcuts(install_base_folder)

    assert mock_copy.called_with(Path.home() / "Desktop", short_cuts_folder)


def _make_files(folder):
    for i in range(3):
        fname = f"file_{i}.txt"
        with open(folder / fname, "w") as fl:
            fl.write(f"a file {i}")


def test_copy_short_cuts(tmp_path):
    source = Path(tmp_path) / "shortcuts"
    source.mkdir(exist_ok=True)

    _make_files(source)

    target = Path(tmp_path) / "target"
    target.mkdir(exist_ok=True)

    _copy_files(target, source)

    assert len(list(target.glob("*.*")))
