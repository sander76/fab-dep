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

EASE_FOLDER = (Path.home()).joinpath(".ease")
FAB_DEPLOY_CONFIG = EASE_FOLDER.joinpath("fab-deploy.json")
TEMP_FOLDER = (Path.home()).joinpath(".ease", "bin")
KEY_EAKEY = "eakey"

LOGGER = logging.getLogger("__name__")

INFO_COLOR = "yellow"
OK_COLOR = "green"
ERROR_COLOR = "red"

jumbo ="""\
  ______      ____ _______ ____   ____  _      
 |  ____/\   |  _ \__   __/ __ \ / __ \| |     
 | |__ /  \  | |_) | | | | |  | | |  | | |     
 |  __/ /\ \ |  _ <  | | | |  | | |  | | |     
 | | / ____ \| |_) | | | | |__| | |__| | |____ 
 |_|/_/    \_\____/  |_|  \____/ \____/|______|
                                               

"""

class Settings(BaseSettings):
    """Fab deploy settings."""

    download_url: str = None
    installation_folder: Path = "/fabricator/"
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
                click.secho(str(err), fg=ERROR_COLOR)
            except FatalEchoException as err:
                click.secho(str(err), fg=ERROR_COLOR)
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


@click.command()
@click.option(
    "--fabfile",
    default=None,
    help="Ease binary. Use when internet connection is not available.",
    type=click.Path(exists=True),
)
@click.option("--key", default=None, help="encryption key")
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
@click.version_option()
def main(fabfile, key, clean, force_download):
    """Main script entry point"""
    EASE_FOLDER.mkdir(exist_ok=True)

    settings: Settings = _load_settings()

    if key:
        click.secho("IMPORTANT !", fg="red")
        click.echo(
            "You have provided a key. This will be stored on the computer"
        )
        click.echo("and used in the future. If you provide the wrong key,")
        click.echo("you can NOT update the tool anymore.")
        click.echo(
            "Only expert center Motors and controls is able to solve this."
        )
        click.echo("")

        if click.confirm("Continue ?", default="n"):
            settings.key = key
            _save_settings(settings)
        else:
            click.echo("Exit installation.")
            return

    key = _load_key(settings)

    _make_temp_folder()

    if fabfile is not None:
        fabfile = Path(fabfile)
    else:
        fabfile = _download_fabfile(
            settings.download_url, force_download=force_download
        )

    decrypted_file = _decrypt(fabfile, key)

    if clean:
        _clean(settings.installation_folder)

    try:
        _extract(decrypted_file, settings.installation_folder)
    except Exception as err:
        click.secho("ERROR extracting archive")
        click.echo(err)

    click.secho("Finished successfully.", fg="green")
    click.secho(
        "Fabricator tool can be found at: {}".format(
            settings.installation_folder
        ),
        fg=INFO_COLOR,
    )


if __name__ == "__main__":
    print(jumbo)
    sys.exit(main())  # pragma: no cover


def _load_key(settings: Settings):
    if settings.key is None:
        click.echo("Key not available. Aborting install.")
        raise Abort()
    return settings.key


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
        dest=dest, dest_basename=dest, size=size / 1024.0 / 1024
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

    return dest


@working_done("Decrypting...")
def _decrypt(aes_file: Path, key):
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
        raise FatalEchoException(
            "An unknown error occurred. Please contact support."
        )
