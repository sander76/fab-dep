import json
from unittest.mock import Mock
from urllib.parse import urljoin

import pytest
import responses
from click import Abort
from click.testing import CliRunner

from fab_deploy.cli import _extract, _decrypt, _clean, _install, _get_latest_url, main
from fab_deploy import cli
from fab_deploy.const import _Settings, _FileSettings
from fab_deploy.download import download_fabfile, download_version_file
from fab_deploy.exceptions import FatalEchoException
from tests.common import HERE

KEY = "abcABC"
ARCHIVE_FILE = HERE.joinpath("test_files", "archive.ease.tar.bz2")
FAB_FILE = HERE.joinpath("test_files", "fabricator.encrypt")
FAKE_FAB_FILE = HERE.joinpath("test_files", "archive.ease_fake.aes")
VERSION_FILE = HERE.joinpath("test_files", "version.json")


DUMMY_DOWNLOAD_URL = "https://motorisation.hde.nl/fabricator/win10/"


@pytest.fixture
def dummy_settings(tmp_path):
    settings = _Settings(
        installation_folder=tmp_path / "install_folder",
        key=KEY,
        download_url=DUMMY_DOWNLOAD_URL,
    )
    settings.installation_folder.mkdir(exist_ok=True, parents=True)
    return settings


@pytest.fixture
def dummy_file_settings(tmp_path):
    _FileSettings.temp_installation_folder = tmp_path.joinpath("temp_install")
    _FileSettings.ease_config_folder = tmp_path.joinpath(".ease")
    file_settings = _FileSettings()

    return file_settings


@pytest.fixture
def mock_settings(monkeypatch, dummy_settings, dummy_file_settings):
    def _load_settings(*args, **kwargs):
        return dummy_settings

    def _get_file_settings(*args, **kwargs):
        return dummy_file_settings

    monkeypatch.setattr("fab_deploy.cli.load_settings", _load_settings)
    monkeypatch.setattr("fab_deploy.cli.get_file_settings", _get_file_settings)


@pytest.fixture
def dummy_version_file(tmp_path):
    return tmp_path / "version.json"


def test_settings():
    settings = _Settings()
    assert settings is not None


def test_extract(dummy_file_settings):

    _extract(ARCHIVE_FILE, dummy_file_settings.temp_installation_folder)

    # assert only one file (the one inside the archive)
    # is in the folder.
    files = list(dummy_file_settings.temp_installation_folder.glob("**/*.*"))
    assert len(files) == 1

    # Add an arbitrary file.
    with open(
        dummy_file_settings.temp_installation_folder.joinpath("out.txt"), "w"
    ) as fl:
        fl.write("a")

    files = list(dummy_file_settings.temp_installation_folder.glob("**/*.*"))
    assert len(files) == 2

    _extract(ARCHIVE_FILE, dummy_file_settings.temp_installation_folder)

    files = list(dummy_file_settings.temp_installation_folder.glob("*.*"))
    assert len(files) == 2

    _clean(dummy_file_settings.temp_installation_folder)
    _extract(ARCHIVE_FILE, dummy_file_settings.temp_installation_folder)
    files = list(dummy_file_settings.temp_installation_folder.glob("*.*"))
    assert len(files) == 1


def test_decrypt_wrong_file(dummy_file_settings, clean):
    """No file to encrypt found"""
    with pytest.raises(FatalEchoException):
        _decrypt(FAKE_FAB_FILE, dummy_file_settings.temp_installation_folder, KEY)


def test_decrypt_file(dummy_file_settings, clean):

    assert dummy_file_settings.temp_installation_folder.exists()
    assert not dummy_file_settings.temp_installation_folder.is_file()

    archive_file = dummy_file_settings.temp_installation_folder.joinpath(
        "fabricator.archive"
    )
    _decrypt(FAB_FILE, archive_file, KEY)

    assert archive_file.exists()


def test_decrypt_wrong_key(dummy_file_settings, clean):
    assert dummy_file_settings.temp_installation_folder.exists()
    assert not dummy_file_settings.temp_installation_folder.is_file()

    key = "wrong_key"
    archive_file = dummy_file_settings.temp_installation_folder.joinpath(
        "fabricator.archive"
    )
    with pytest.raises(FatalEchoException):
        _decrypt(FAB_FILE, archive_file, key)


@responses.activate
def test_download_fab_file(dummy_file_settings, clean, dummy_settings):

    # dummy_settings.download_url = "https://google.com"
    responses.add(responses.GET, dummy_settings.download_url, status=404)

    fab_file = dummy_file_settings.temp_installation_folder.joinpath(
        "fabricator.encrypt"
    )
    with pytest.raises(FatalEchoException):
        download_fabfile(dummy_settings.download_url, fab_file)


def test__install(dummy_settings, mock_settings, dummy_file_settings):

    _install(
        FAB_FILE, True, dummy_settings, dummy_file_settings.temp_installation_folder
    )

    files = list(dummy_settings.installation_folder.glob("**/*.*"))
    assert len(files) > 0


@pytest.fixture
def mock_download_version_file(monkeypatch):
    def version_file(download_url, dest_file):
        with open(VERSION_FILE) as fl:
            _js = json.load(fl)
        with open(dest_file, "w") as fl:
            json.dump(_js, fl)
        return dest_file

    monkeypatch.setattr("fab_deploy.cli.download_version_file", version_file)


@pytest.fixture
def mock_download_fabfile(monkeypatch):
    mock = Mock()

    monkeypatch.setattr("fab_deploy.cli.download_fabfile", mock)
    return mock


@pytest.fixture
def mock_install_function(monkeypatch):
    mock_install = Mock()

    monkeypatch.setattr("fab_deploy.cli._install", mock_install)
    return mock_install


def mock_check_running(*args, **kwargs):
    pass


def test_cli_file(
    mock_settings, dummy_file_settings, dummy_settings, mock_install_function
):
    cli.check_running = mock_check_running
    runner = CliRunner()
    result = runner.invoke(main, ["install", "from-file", str(FAB_FILE)])

    mock_install_function.assert_called_with(
        FAB_FILE,
        True,
        dummy_settings,
        dummy_file_settings.temp_installation_folder,
    )
    assert result.exit_code == 0


def test_cli_download(
    mock_settings,
    dummy_file_settings,
    dummy_settings,
    mock_download_version_file,
    mock_download_fabfile,
    mock_install_function,
):
    cli.check_running = mock_check_running
    fab_encrypted = dummy_file_settings.temp_installation_folder.joinpath(
        "fabricator.encrypt"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["install", "download"])

    assert dummy_file_settings.version_file.exists()

    mock_download_fabfile.assert_called_with(
        "https://motorisation.hde.nl/fabricator/win10/win10-fabricator-app0.11-ease1.0.fab",
        fab_encrypted,
        force_download=True,
    )

    mock_install_function.assert_called_with(
        fab_encrypted,
        True,
        dummy_settings,
        dummy_file_settings.temp_installation_folder,
    )

    assert result.exit_code == 0


def test_get_latest_url(dummy_settings):
    latest = _get_latest_url(dummy_settings.download_url, VERSION_FILE)

    assert (
        latest
        == "https://motorisation.hde.nl/fabricator/win10/win10-fabricator-app0.11-ease1.0.fab"
    )
