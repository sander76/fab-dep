# -*- coding: utf-8 -*-
"""Console script for fab-deploy."""
import json
import shutil
import sys

from pathlib import Path
from urllib.parse import urljoin
import click

from click import Abort
from pydantic import BaseSettings

from fab_deploy.const import (
    EASE_CONFIG_FOLDER,
    INSTALLATION_FOLDER,
    FAB_DEPLOY_CONFIG,
    TEMP_FOLDER,
    LOGGER,
    INFO_COLOR,
    ERROR_COLOR,
)
from fab_deploy.crypto import decryptFile
from fab_deploy.download import _download_fabfile, _download_version_file

# KEY_EAKEY = "eakey"

jumbo = r"""
  ______      ____ _______ ____   ____  _      
 |  ____/\   |  _ \__   __/ __ \ / __ \| |     
 | |__ /  \  | |_) | | | | |  | | |  | | |     
 |  __/ /\ \ |  _ <  | | | |  | | |  | | |     
 | | / ____ \| |_) | | | | |__| | |__| | |____ 
 |_|/_/    \_\____/  |_|  \____/ \____/|______|
                                               

"""

click.echo(jumbo)


class Settings(BaseSettings):
    """Fab deploy settings.

    download_url: # URL base folder where binaries and version info is stored.
    """

    download_url: str = None
    installation_folder: Path = INSTALLATION_FOLDER
    key: str = None


class EchoException(Exception):
    pass


class FatalEchoException(Exception):
    pass


def working_done(message, done="done."):
    def _echoer(func):
        def _wrapper(*args, **kwargs):

            click.secho(message, fg=INFO_COLOR, nl=False)
            try:
                result = func(*args, **kwargs)
            except EchoException as err:
                click.secho(str(err), bg=ERROR_COLOR)
            except FatalEchoException as err:
                click.secho(str(err), bg=ERROR_COLOR)
                raise Abort()
            else:
                click.secho(done, fg=INFO_COLOR)
                return result

        return _wrapper

    return _echoer


@working_done("Saving config...")
def _save_settings(settings: Settings):
    with open(FAB_DEPLOY_CONFIG, "w") as fl:
        fl.write(settings.json())


@working_done("Loading config...")
def _load_settings():
    if not FAB_DEPLOY_CONFIG.exists():
        click.secho(
            "file does exist yet. loading default...", nl=False, fg=INFO_COLOR
        )
        return Settings()
    with open(FAB_DEPLOY_CONFIG) as fl:
        dct = json.load(fl)
    settings = Settings(**dct)
    return settings


def _check_key(settings: Settings):
    if settings.key is None:
        click.secho("----------------------------------", bg=ERROR_COLOR)
        click.secho("Error: Encryption key not provided", bg=ERROR_COLOR)
        click.secho("----------------------------------", bg=ERROR_COLOR)
        click.secho("Please provide an encryption key:", bg=ERROR_COLOR)
        click.secho("enter <fab --help> to get assistance", bg=ERROR_COLOR)
        raise Abort()


def _validate_folders(
    temp_folder: Path, installation_folder: Path, ease_config_folder: Path
):
    temp_folder.mkdir(exist_ok=True, parents=True)
    installation_folder.mkdir(exist_ok=True, parents=True)
    ease_config_folder.mkdir(exist_ok=True, parents=True)


def _install(fabfile: Path, clean, settings):
    if clean:
        _clean(settings.installation_folder)

    decrypted_file = _decrypt(fabfile, settings.key)

    _extract(decrypted_file, settings.installation_folder)

    click.secho("Finished successfully.", fg="green")
    click.secho(
        "Fabricator tool can be found at: {}".format(
            settings.installation_folder
        ),
        fg=INFO_COLOR,
    )


def _get_latest_url(base_url: Settings, json_file) -> str:
    """Get the filename of the latest fabricator release."""
    with open(json_file) as fl:
        _version = json.load(fl)

    latest = _version["latest"]
    return urljoin(base_url.download_url, latest)


@working_done("Decrypting...")
def _decrypt(aes_file: Path, key) -> Path:
    buffer_size = 64 * 1024

    temp_file = TEMP_FOLDER.joinpath("archive.ease")

    if not aes_file.exists():
        raise FatalEchoException("Encrypted file not found")

    try:
        decryptFile(str(aes_file), str(temp_file), key, buffer_size)
    except PermissionError:
        raise FatalEchoException("permission error")
    except ValueError as err:
        raise FatalEchoException(err)

    return temp_file


@working_done("Cleaning output folder...")
def _clean(output_folder: Path):
    click.secho("Cleaning installation folder.")
    try:
        shutil.rmtree(output_folder)
    except FileNotFoundError:
        click.secho("Folder does not exist. Continueing", fg=INFO_COLOR)


@working_done("Extracting archive...")
def _extract(archive, output_folder):
    try:
        shutil.unpack_archive(archive, output_folder, "bztar")

    except Exception as err:
        LOGGER.exception(err)
        click.secho(err)
        raise Abort()


@click.command()
@click.option(
    "--clean",
    default=False,
    help="clear the installation folder first",
    is_flag=True,
)
@click.option(
    "--force_download",
    default=False,
    help="Always download the binary. Overwriting an existing one.",
    is_flag=True,
)
def install(clean, force_download):
    """Install the fabricator tool using a download link."""

    settings: Settings = _load_settings()

    _check_key(settings)

    if settings.download_url is None:
        click.secho("-----------------------", bg="red")
        click.secho("Error: No URL provided.", bg="red")
        click.secho("-----------------------", bg="red")
        click.echo("")
        click.secho("Use <fab --help> for help.")
        raise Abort()

    _validate_folders(TEMP_FOLDER, INSTALLATION_FOLDER, EASE_CONFIG_FOLDER)

    version_file = _download_version_file(settings.download_url)
    binary_url = _get_latest_url(settings, version_file)

    fabfile = _download_fabfile(binary_url, force_download=force_download)

    _install(fabfile, clean, settings)


@click.command()
@click.argument("file", type=click.Path(exists=True))
def from_file(file):
    """Install fabricator using a provided binary file."""
    settings: Settings = _load_settings()
    _check_key(settings)

    fabfile = Path(file)

    _validate_folders(TEMP_FOLDER, INSTALLATION_FOLDER, EASE_CONFIG_FOLDER)

    _install(fabfile, True, settings)


@click.command()
@click.argument("key", type=click.STRING)
def set_key(key: str):
    """Set an encryption key"""
    settings: Settings = _load_settings()
    settings.key = key
    _save_settings(settings)
    click.secho("Encryption key saved.", fg="green")
    click.secho(key, fg="green")


@click.command()
@click.argument("download_url")
def set_url(download_url: str):
    """Set a URL to check for updates."""
    settings: Settings = _load_settings()

    settings.download_url = download_url
    _save_settings(settings)

    click.secho("Download url saved.", fg="green")
    click.secho(download_url, fg="green")


@click.version_option()
@click.group()
def main():
    """Fabtool main entrypoint"""


main.add_command(install)
main.add_command(set_key)
main.add_command(set_url)

if __name__ == "__main__":
    # print(jumbo)
    sys.exit(main())  # pragma: no cover
