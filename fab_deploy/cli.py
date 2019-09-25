# -*- coding: utf-8 -*-
"""Console script for fab-deploy."""
import json
import shutil
import sys
import logging
from pathlib import Path
from urllib.parse import urljoin
import click
from . import __version__

from click import Abort
from pydantic import BaseSettings

from fab_deploy.const import (
    INFO_COLOR,
    ERROR_COLOR,
    load_settings,
    get_file_settings,
    save_settings,
)
import fab_deploy.shortcuts as shortcuts
from fab_deploy.crypto import decryptFile
from fab_deploy.download import download_fabfile, download_version_file

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fab_deploy.const import _Settings, _FileSettings


LOGGER = logging.getLogger(__name__)

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


def _check_key(settings: "_Settings"):
    if settings.key is None:
        click.secho("----------------------------------", bg=ERROR_COLOR)
        click.secho("Error: Encryption key not provided", bg=ERROR_COLOR)
        click.secho("----------------------------------", bg=ERROR_COLOR)
        click.secho("Please provide an encryption key:", bg=ERROR_COLOR)
        click.secho("enter <fab --help> to get assistance", bg=ERROR_COLOR)
        raise Abort()


def _install(fabfile: Path, clean, settings, temp_folder: Path, copy_shortcuts):
    if clean:
        _clean(settings.installation_folder)

    archive_file = temp_folder.joinpath("fabricator.archive")
    _decrypt(fabfile, archive_file, settings.key)

    _extract(archive_file, settings.installation_folder)

    click.secho("Finished successfully.", fg="green")
    click.secho(
        "Fabricator tool can be found at: {}".format(settings.installation_folder),
        fg=INFO_COLOR,
    )
    if copy_shortcuts:
        shortcuts.copy_shortcuts(settings.installation_folder)


def _get_latest_url(settings: "_Settings", json_file) -> str:
    """Get the filename of the latest fabricator release."""
    with open(json_file) as fl:
        _version = json.load(fl)

    latest = _version["latest"]
    return urljoin(settings.download_url, latest)


@working_done("Decrypting...")
def _decrypt(in_file: Path, out_file: Path, key) -> Path:
    buffer_size = 64 * 1024

    if not in_file.exists():
        raise FatalEchoException("Encrypted file not found")

    try:
        decryptFile(str(in_file), str(out_file), key, buffer_size)
    except PermissionError:
        raise FatalEchoException("permission error")
    except ValueError as err:
        raise FatalEchoException(err)

    return out_file


@working_done("Cleaning output folder...")
def _clean(output_folder: Path):
    click.secho("Cleaning installation folder.")
    try:
        shutil.rmtree(output_folder)
    except FileNotFoundError:
        click.secho("Folder does not exist. Continueing", fg=INFO_COLOR)
    except PermissionError:
        click.secho(
            "Unable to clear installation folder. Did you close the fabricator ?",
            bg=ERROR_COLOR,
        )


@working_done("Extracting archive...")
def _extract(archive, output_folder):
    try:
        shutil.unpack_archive(archive, output_folder, "bztar")

    except Exception as err:
        LOGGER.exception(err)
        click.secho(err)
        raise Abort()


@click.group()
@click.option(
    "--clean", default=False, help="clear the installation folder first", is_flag=True
)
@click.option(
    "--shortcut", default=False, help="make app shortcuts to the desktop", is_flag=True
)
@click.pass_context
def install(ctx, clean, shortcut):
    """Install the fabricator tool."""
    file_settings = get_file_settings()
    settings = load_settings(file_settings.config_file)

    # ctx.file_settings = file_settings
    ctx.obj = {
        "settings": settings,
        "file_settings": file_settings,
        "shortcut": shortcut,
    }

    _check_key(settings)


@install.command()
@click.pass_context
def download(ctx):
    """Use download location."""
    settings = ctx.obj.get("settings")
    file_settings: "_FileSettings" = ctx.obj.get("file_settings")

    if settings.download_url is None:
        click.secho("-----------------------", bg="red")
        click.secho("Error: No URL provided.", bg="red")
        click.secho("-----------------------", bg="red")
        click.echo("")
        click.secho("Use <fab --help> for help.")
        raise Abort()
    click.secho("downloading version file {}".format(str(file_settings.version_file)))
    version_file = download_version_file(
        settings.download_url, file_settings.version_file
    )
    binary_url = _get_latest_url(settings, version_file)
    click.secho("downloading binary {}".format(str(binary_url)))
    fabfile = file_settings.temp_installation_folder.joinpath("fabricator.encrypt")
    download_fabfile(binary_url, fabfile, force_download=True)

    copy_shortcut = ctx.obj.get("shortcut")

    _install(
        fabfile, True, settings, file_settings.temp_installation_folder, copy_shortcut
    )


@install.command()
@click.argument("file", type=click.Path(exists=True))
@click.pass_context
def from_file(ctx, file):
    """Install fabricator using a provided binary file."""
    fabfile = Path(file)

    settings: "_Settings" = ctx.obj.get("settings")
    file_settings: "_FileSettings" = ctx.obj.get("file_settings")

    copy_shortcut = ctx.obj.get("shortcut")

    _install(
        fabfile, True, settings, file_settings.temp_installation_folder, copy_shortcut
    )


@click.command()
@click.argument("key", type=click.STRING)
def set_key(key: str):
    """Set an encryption key"""
    file_settings = get_file_settings()
    settings = load_settings(file_settings.config_file)
    settings.key = key

    save_settings(settings, file_settings.config_file)

    click.secho("Encryption key saved.", fg="green")
    click.secho(key, fg="green")


@click.command()
@click.argument("download_url")
def set_url(download_url: str):
    """Provide the full URL to check for updates."""
    file_settings = get_file_settings()
    settings = load_settings(file_settings.config_file)

    settings.download_url = download_url
    save_settings(settings, file_settings.config_file)

    click.secho("Download url saved.", fg="green")
    click.secho(download_url, fg="green")


@click.version_option(version=__version__)
@click.group()
def main():
    """Fabtool main entrypoint"""


main.add_command(install)
main.add_command(set_key)
main.add_command(set_url)

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
