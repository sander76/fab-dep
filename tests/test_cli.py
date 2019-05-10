import pytest
import responses
from click import Abort

from fab_deploy.cli import (
    _make_temp_folder,
    _extract,
    _decrypt,
    _load_settings,
    _download_fabfile,
    _clean)
from tests.common import TEST_TEMP_FOLDER, HERE

ARCHIVE_FILE = HERE.joinpath("test_files", "archive.ease.tar.bz2")
AES_FILE = HERE.joinpath("test_files", "archive.ease.aes")
FAKE_AES_FILE = HERE.joinpath("test_files", "archive.ease_fake.aes")
FAKE_CONFIG_FILE = TEST_TEMP_FOLDER.joinpath("fab_config.json")


@pytest.fixture
def fake_temp_folder(monkeypatch):
    monkeypatch.setattr("fab_deploy.cli.TEMP_FOLDER", TEST_TEMP_FOLDER)
    monkeypatch.setattr("fab_deploy.cli.FAB_DEPLOY_CONFIG", FAKE_CONFIG_FILE)


def test_make_temp_folder(fake_temp_folder, clean):
    _make_temp_folder()

    assert TEST_TEMP_FOLDER.exists()
    assert not TEST_TEMP_FOLDER.is_file()


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


KEY = "abcABC"


def test_decrypt_wrong_file(fake_temp_folder, clean):
    """No file to encrypt found"""
    with pytest.raises(Abort):
        _decrypt(FAKE_AES_FILE, KEY)


def test_decrypt_file(fake_temp_folder, clean):
    TEST_TEMP_FOLDER.mkdir(exist_ok=True, parents=True)

    assert TEST_TEMP_FOLDER.exists()
    assert not TEST_TEMP_FOLDER.is_file()

    fl = _decrypt(AES_FILE, KEY)

    assert fl == TEST_TEMP_FOLDER.joinpath("archive.ease")

def test_decrypt_wrong_key(fake_temp_folder,clean):
    TEST_TEMP_FOLDER.mkdir(exist_ok=True, parents=True)

    assert TEST_TEMP_FOLDER.exists()
    assert not TEST_TEMP_FOLDER.is_file()

    key = "wrong_key"

    with pytest.raises(Abort):
        fl = _decrypt(AES_FILE, key)

@responses.activate
def test_download_fab_file(fake_temp_folder, clean):
    settings = _load_settings()
    responses.add(responses.GET, settings.download_url, status=404)

    with pytest.raises(Abort):
        _download_fabfile(settings.download_url)


def test_cli():
    pass
