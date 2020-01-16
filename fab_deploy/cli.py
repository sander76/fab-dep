# -*- coding: utf-8 -*-
"""Console script for fab-deploy."""
import functools
import json
import shutil
import sys
import logging
from pathlib import Path
from sys import platform
from time import sleep
from urllib.parse import urljoin
import click
import psutil
from click import Abort

from fab_deploy.bootstrap import execute_bootstrap
from fab_deploy.exceptions import EchoException, FatalEchoException
from . import __version__

# from click import Abort
# from pydantic import BaseSettings

from fab_deploy.const import (
    INFO_COLOR,
    ERROR_COLOR,
    load_settings,
    get_file_settings,
    save_settings,
    KEY_PLATFORM,
    KEY_WINDOWS,
    KEY_LINUX,
)

from fab_deploy.crypto import decryptFile
from fab_deploy.download import download_fabfile, download_version_file

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fab_deploy.const import _Settings, _FileSettings


LOGGER = logging.getLogger(__name__)

jumbo = r"""
  ______      ____ _______ ____   ____  _      
 |  ____/\   |  _ \__   __/ __ \ / __ \| |     
 | |__ /  \  | |_) | | | | |  | | |  | | |     
 |  __/ /\ \ |  _ <  | | | |  | | |  | | |     
 | | / ____ \| |_) | | | | |__| | |__| | |____ 
 |_|/_/    \_\____/  |_|  \____/ \____/|______|manager
                                               

"""

click.echo(jumbo)


def working_done(message, done="done."):
    def _echoer(func):
        def _wrapper(*args, **kwargs):

            click.secho(message, fg=INFO_COLOR, nl=False)
            try:
                result = func(*args, **kwargs)
            except EchoException as err:
                click.secho(str(err), bg=ERROR_COLOR)
            # except FatalEchoException as err:
            #     click.secho(str(err), bg=ERROR_COLOR)
            #     raise
            else:
                click.secho(done, fg=INFO_COLOR)
                return result

        return _wrapper

    return _echoer


def check_running():
    """check whether the FABtool is running."""
    name = None
    if KEY_PLATFORM == KEY_WINDOWS:
        name = "fabricator.exe"
    elif KEY_PLATFORM == KEY_LINUX:
        name = "fabricator"
    if name is None:
        raise FatalEchoException("Tool should be running on either windows or linux")

    for pid in psutil.pids():
        p = psutil.Process(pid)
        if p.name() == name:
            raise FatalEchoException(
                "FABtool is running. Please close it first before updating"
            )


def closed_delay(delay=5):
    for i in range(delay, 0, -1):
        print(f"closing in {i} seconds\r", end="", flush=True)
        sleep(1)


def _check_key(settings: "_Settings"):
    if settings.key is None:
        click.secho("----------------------------------", bg=ERROR_COLOR)
        click.secho("Error: Encryption key not provided", bg=ERROR_COLOR)
        click.secho("----------------------------------", bg=ERROR_COLOR)
        click.secho("Please provide an encryption key:", bg=ERROR_COLOR)
        click.secho("enter <fab --help> to get assistance", bg=ERROR_COLOR)
        raise FatalEchoException()


def _install(fabfile: Path, clean, settings, temp_folder: Path):
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


def _get_latest_url(download_folder: str, json_file) -> str:
    """Get the filename of the latest fabricator release."""
    with open(json_file) as fl:
        _version = json.load(fl)

    latest = _version["latest"]
    return urljoin(download_folder, latest)


def fatal_handler(func):
    """Wrapper that catches fatal errors and displays them."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except FatalEchoException as err:
            click.secho(30 * "-", fg=ERROR_COLOR, bold=True)
            click.secho("  ## PROBLEM !! ##", bg=ERROR_COLOR, fg="white", bold=True)
            click.secho(30 * "-", fg=ERROR_COLOR, bold=True)
            click.secho("  " + str(err), bold=True)
            click.secho(30 * "-", fg=ERROR_COLOR, bold=True)
            click.echo("")
            click.prompt("ENTER to EXIT", default="")
            raise Abort()

    return wrapper


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
        raise FatalEchoException(
            "Unable to clear installation folder. Did you close the fabricator ?"
        )


@working_done("Extracting archive...")
def _extract(archive, output_folder):
    try:
        shutil.unpack_archive(archive, output_folder, "bztar")

    except Exception as err:
        LOGGER.exception(err)
        raise FatalEchoException(err)


@click.group()
@click.option(
    "--clean", default=False, help="clear the installation folder first", is_flag=True
)
@click.option("--bootstrap", default=False, help="bootstrap the app", is_flag=True)
@click.pass_context
@fatal_handler
def install(ctx, clean, bootstrap):
    """Install the fabricator tool."""
    check_running()
    file_settings = get_file_settings()
    settings = load_settings(file_settings.config_file)
    ctx.obj = {
        "settings": settings,
        "file_settings": file_settings,
        "bootstrap": bootstrap,
    }

    _check_key(settings)


@install.command()
@click.pass_context
@click.option(
    "--channel",
    default=None,
    help="install from a specific channel. If omitted release channel is used.",
)
@fatal_handler
def download(ctx, channel=None):
    """Install fabtool by automatically downloading and installing it.

    :param channel: Install from a specific channel. If omitted the release channel
        is used. A release channel is basically a folder which get appended to the
        base download url.
    """
    settings = ctx.obj.get("settings")
    file_settings: "_FileSettings" = ctx.obj.get("file_settings")

    if settings.download_url is None:
        click.secho("-----------------------", bg="red")
        click.secho("Error: No URL provided.", bg="red")
        click.secho("-----------------------", bg="red")
        click.echo("")
        click.secho("Use <fab --help> for help.")
        raise FatalEchoException()
    click.secho("downloading version file {}".format(str(file_settings.version_file)))

    if channel:
        download_url = f"{settings.download_url}/{channel}/"
    else:
        download_url = settings.download_url

    version_file = download_version_file(download_url, file_settings.version_file)
    binary_url = _get_latest_url(download_url, version_file)
    click.secho("downloading binary {}".format(str(binary_url)))
    fabfile = file_settings.temp_installation_folder.joinpath("fabricator.encrypt")
    download_fabfile(binary_url, fabfile)

    _install(fabfile, True, settings, file_settings.temp_installation_folder)

    closed_delay()


@install.command()
@click.argument("file", type=click.Path(exists=True))
@click.pass_context
@fatal_handler
def from_file(ctx, file):
    """Install fabricator using a provided binary file."""
    fabfile = Path(file)

    settings: "_Settings" = ctx.obj.get("settings")
    file_settings: "_FileSettings" = ctx.obj.get("file_settings")

    _install(fabfile, True, settings, file_settings.temp_installation_folder)


def _set_key(key: str):
    if len(key) != 64:
        raise FatalEchoException("Key length incorrect.")
    file_settings = get_file_settings()
    settings = load_settings(file_settings.config_file)
    settings.key = key

    save_settings(settings, file_settings.config_file)

    click.secho("Encryption key saved.", fg="green")
    click.secho(key, fg="green")
    return key


@click.command()
@click.argument("key", type=click.STRING)
@fatal_handler
def set_key(key: str):
    """Set an encryption key"""
    _set_key(key)


def _auto_load(folder: Path):
    txt = folder / "key.txt"
    if not txt.exists():
        raise FatalEchoException(f"No key found. {txt}")

    with open(txt) as fl:
        _key = fl.read()

    return _key


@click.command()
@fatal_handler
def auto_load():
    """Look in the current folder for a key.txt file and automatically processes it."""

    current_folder = Path.cwd()
    click.secho(f"Current working folder {current_folder}")

    _key = _auto_load(current_folder)
    _set_key(_key)


@click.command()
@click.argument("download_url")
@fatal_handler
def set_url(download_url: str):
    """Provide the full URL to check for updates."""
    file_settings = get_file_settings()
    settings = load_settings(file_settings.config_file)

    settings.download_url = download_url
    save_settings(settings, file_settings.config_file)

    click.secho("Download url saved.", fg="green")
    click.secho(download_url, fg="green")


@click.command()
@fatal_handler
def bootstrap():

    """Prepare the fabricator app for usage."""
    file_settings = get_file_settings()
    settings = load_settings(file_settings.config_file)
    execute_bootstrap(settings.installation_folder)


@click.version_option(version=__version__)
@click.group()
def main():
    """Fabtool main entrypoint"""


main.add_command(install)
main.add_command(set_key)
main.add_command(auto_load)
main.add_command(set_url)
main.add_command(bootstrap)

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
