import logging

# from fab_deploy.const import platform
from fab_deploy.const import load_settings

_LOGGER = logging.getLogger(__name__)


def test_settings_linux_url(monkeypatch, tmp_path):
    monkeypatch.setattr("fab_deploy.const.platform", "linux")

    settings = load_settings(tmp_path / "settings.json")

    assert (
        settings.download_url
        == "https://motorisation.hde.nl/bin/fabricator/ubuntu18_04/"
    )


def test_settings_win_url(monkeypatch, tmp_path):
    monkeypatch.setattr("fab_deploy.const.platform", "win32")

    settings = load_settings(tmp_path / "settings.json")

    assert settings.download_url == "https://motorisation.hde.nl/bin/fabricator/win10/"
