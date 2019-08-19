# -*- coding: utf-8 -*-
"""Console script for fab-deploy."""
import json
import logging
import os
import shutil
import sys
from pathlib import Path

import click

import requests
from click import Abort
from pydantic import BaseSettings

from fab_deploy.crypto import decryptFile

EASE_CONFIG_FOLDER = (Path.home()).joinpath(".ease")
INSTALLATION_FOLDER = (Path.home()).joinpath("fabricator")

FAB_DEPLOY_CONFIG = EASE_CONFIG_FOLDER.joinpath("fab-deploy.json")
TEMP_FOLDER = (Path.home()).joinpath(".ease", "bin")
# KEY_EAKEY = "eakey"

LOGGER = logging.getLogger("__name__")

INFO_COLOR = "cyan"
OK_COLOR = "green"
ERROR_COLOR = "red"

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
    """Fab deploy settings."""

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


# def _decrypt(fabfile:Path)


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

    EASE_CONFIG_FOLDER.mkdir(exist_ok=True)

    settings: Settings = _load_settings()

    _check_key(settings)

    if settings.download_url is None:
        click.secho("-----------------------", bg="red")
        click.secho("Error: No URL provided.", bg="red")
        click.secho("-----------------------", bg="red")
        click.echo("")
        click.secho("Use <fab --help> for help.")
        raise Abort()

    _make_temp_folder()

    fabfile = _download_fabfile(
        settings.download_url, force_download=force_download
    )

    _install(fabfile, clean, settings)


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


@click.command()
@click.argument("file", type=click.Path(exists=True))
def from_file(file):
    fabfile = Path(file)

    EASE_CONFIG_FOLDER.mkdir(exist_ok=True)

    settings: Settings = _load_settings()

    _check_key(settings)
    _make_temp_folder()

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


def _make_temp_folder():
    TEMP_FOLDER.mkdir(exist_ok=True, parents=True)


def _download_fabfile(download_url: str, force_download=False):

    return _download_file(
        download_url,
        TEMP_FOLDER.joinpath("fabricator.ease"),
        force_download=force_download,
    )


def _download_file(
    url,
    dest: Path,
    chunk_size=1024,
    force_download=False,
    label="Downloading {dest_basename} ({size:.2f}MB)",
) -> Path:

    click.secho("Downloading binary...", fg=INFO_COLOR)
    if dest.exists():
        if not force_download:

            if not click.confirm(
                "File already exists. Replace {}?".format(dest)
            ):
                return dest
    try:
        request = requests.get(url, stream=True)
    except requests.exceptions.ConnectionError as err:
        click.secho("ERROR: Unable to make a connection")
        LOGGER.exception(err)
        raise Abort()

    if request.status_code not in (200, 201, 202):
        click.secho("ERROR: Unable to reach download target")
        LOGGER.error(request)
        raise Abort()

    size = int(request.headers.get("content-length"))
    label = label.format(
        dest=dest, dest_basename=dest.name, size=size / 1024.0 / 1024
    )
    with click.open_file(dest, "wb") as f:
        content_iter = request.iter_content(chunk_size=chunk_size)
        with click.progressbar(
            content_iter, length=size / 1024, label=label
        ) as bar:
            for chunk in bar:
                if chunk:
                    f.write(chunk)
                    # f.flush()
    click.secho("Finished. Saved {}".format(dest))
    return dest


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
def _clean(output_folder):
    shutil.rmtree(output_folder)


@working_done("Extracting archive...")
def _extract(archive, output_folder):
    try:
        shutil.unpack_archive(archive, output_folder, "bztar")

    except Exception as err:
        LOGGER.exception(err)
        click.secho(err)
        raise Abort()


if __name__ == "__main__":
    # print(jumbo)
    sys.exit(main())  # pragma: no cover
