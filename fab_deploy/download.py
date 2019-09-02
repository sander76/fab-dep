"""Download things."""

import logging
from pathlib import Path
from urllib.parse import urljoin

import click
import requests
from click import Abort

from fab_deploy.const import INFO_COLOR, ERROR_COLOR

_LOGGER = logging.getLogger(__name__)


def download_fabfile(download_url: str, dest: Path, force_download=True):

    return _download_file(download_url, dest, force_download=force_download)


def download_version_file(download_url: str, dest: Path):
    version_url = urljoin(download_url, "version.json")
    return _download_file(version_url, dest, force_download=True)


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

            if not click.confirm("File already exists. Replace {}?".format(dest)):
                return dest
    try:
        request = requests.get(url, stream=True)
    except requests.exceptions.ConnectionError as err:
        click.secho("ERROR: Unable to make a connection")
        _LOGGER.exception(err)
        raise Abort()

    if request.status_code not in (200, 201, 202):
        click.secho("ERROR: Unable to reach download target")
        _LOGGER.error(request)
        click.secho(f"Cannot find {url}", bg=ERROR_COLOR)
        raise Abort()

    size = int(request.headers.get("content-length"))
    label = label.format(dest=dest, dest_basename=dest.name, size=size / 1024.0 / 1024)
    with click.open_file(dest, "wb") as f:
        content_iter = request.iter_content(chunk_size=chunk_size)
        with click.progressbar(content_iter, length=size / 1024, label=label) as bar:
            for chunk in bar:
                if chunk:
                    f.write(chunk)
                    # f.flush()
    click.secho("Finished. Saved {}".format(dest))
    return dest
