from urllib.parse import urljoin

import pytest
import responses
from click import Abort

from fab_deploy.cli import (
    _extract,
    _decrypt,
    _load_settings,
    _clean,
    Settings,
    _install,
    _get_latest_url, _validate_folders)
from fab_deploy.download import _download_fabfile, _download_version_file
from tests.common import TEST_TEMP_FOLDER, HERE

KEY = "abcABC"
ARCHIVE_FILE = HERE.joinpath("test_files", "archive.ease.tar.bz2")
FAB_FILE = HERE.joinpath("test_files", "archive.ease.aes")
FAKE_FAB_FILE = HERE.joinpath("test_files", "archive.ease_fake.aes")
VERSION_FILE = HERE.joinpath("test_files", "version.json")

FAKE_CONFIG_FILE = TEST_TEMP_FOLDER.joinpath("fab_config.json")

DUMMY_DOWNLOAD_URL="https://motorisation.hde.nl/fabricator/win10/"

@pytest.fixture
def fake_temp_folder(monkeypatch):
    monkeypatch.setattr("fab_deploy.cli.TEMP_FOLDER", TEST_TEMP_FOLDER)
    monkeypatch.setattr("fab_deploy.cli.FAB_DEPLOY_CONFIG", FAKE_CONFIG_FILE)


@pytest.fixture
def dummy_settings(tmp_path):
    settings = Settings(
        installation_folder=tmp_path / "install_folder",
        key=KEY,
        download_url=DUMMY_DOWNLOAD_URL,
    )
    return settings


@pytest.fixture
def dummy_version_file(tmp_path):
    return tmp_path / "version.json"





def test_extract(fake_temp_folder, clean):

    assert not TEST_TEMP_FOLDER.exists()

    _extract(ARCHIVE_FILE, TEST_TEMP_FOLDER)
    assert TEST_TEMP_FOLDER.exists()

    # assert only one file (the one inside the archive)
    # is in the folder.
    files = list(TEST_TEMP_FOLDER.glob("*.*"))
    assert len(files) == 1

    # Add an arbitrary file.
    with open(TEST_TEMP_FOLDER.joinpath("out.txt"), "w") as fl:
        fl.write("a")

    files = list(TEST_TEMP_FOLDER.glob("*.*"))
    assert len(files) == 2

    _extract(ARCHIVE_FILE, TEST_TEMP_FOLDER)

    files = list(TEST_TEMP_FOLDER.glob("*.*"))
    assert len(files) == 2

    _clean(TEST_TEMP_FOLDER)
    _extract(ARCHIVE_FILE, TEST_TEMP_FOLDER)
    files = list(TEST_TEMP_FOLDER.glob("*.*"))
    assert len(files) == 1


def test_decrypt_wrong_file(fake_temp_folder, clean):
    """No file to encrypt found"""
    with pytest.raises(Abort):
        _decrypt(FAKE_FAB_FILE, KEY)


def test_decrypt_file(fake_temp_folder, clean):
    TEST_TEMP_FOLDER.mkdir(exist_ok=True, parents=True)

    assert TEST_TEMP_FOLDER.exists()
    assert not TEST_TEMP_FOLDER.is_file()

    fl = _decrypt(FAB_FILE, KEY)

    assert fl == TEST_TEMP_FOLDER.joinpath("archive.ease")


def test_decrypt_wrong_key(fake_temp_folder, clean):
    TEST_TEMP_FOLDER.mkdir(exist_ok=True, parents=True)

    assert TEST_TEMP_FOLDER.exists()
    assert not TEST_TEMP_FOLDER.is_file()

    key = "wrong_key"

    with pytest.raises(Abort):
        fl = _decrypt(FAB_FILE, key)


@responses.activate
def test_download_fab_file(fake_temp_folder, clean, dummy_settings):

    #dummy_settings.download_url = "https://google.com"
    responses.add(responses.GET, dummy_settings.download_url, status=404)

    with pytest.raises(Abort):
        _download_fabfile(dummy_settings.download_url)


def test__install(dummy_settings: Settings, fake_temp_folder):
    assert not dummy_settings.installation_folder.exists()

    _validate_folders()
    _install(FAB_FILE, True, dummy_settings)

    assert dummy_settings.installation_folder.exists()

    files = list(dummy_settings.installation_folder.glob("**/*.*"))
    assert len(files) > 0


def test_cli():
    pass


def test_get_latest_url(dummy_settings):
    latest = _get_latest_url(dummy_settings,VERSION_FILE)

    assert latest == "https://motorisation.hde.nl/fabricator/win10/win10-fabricator-app0.11-ease1.0.fab"
