"""Download things."""

import logging
from pathlib import Path
from urllib.parse import urljoin

import click
import requests

# from click import Abort

from fab_deploy.const import INFO_COLOR, ERROR_COLOR
from fab_deploy.exceptions import FatalEchoException

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
    label="Downloading ({size:.2f}MB)",
) -> Path:

    if dest.exists():
        if not force_download:

            if not click.confirm("File already exists. Replace {}?".format(dest)):
                return dest
    try:
        request = requests.get(url, stream=True)
    except requests.exceptions.ConnectionError as err:
        _LOGGER.exception(err)
        raise FatalEchoException(f"Unable to make a connection {url}")

    if request.status_code not in (200, 201, 202):
        _LOGGER.error(request)
        raise FatalEchoException(
            f"Unable to connect to {url} status code {request.status_code}"
        )

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
