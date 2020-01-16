import logging
from pathlib import Path
from sys import platform
import subprocess

from fab_deploy.exceptions import FatalEchoException

_LOGGER = logging.getLogger(__name__)
#
# def _run(*args, cwd=app_folder, capture_output=True, desc=None):
#     if desc:
#         message = desc
#     else:
#         message = str(args)
#
#     click.secho(message, nl=False, fg=CLICK_INFO_COLOR)
#
#     process = subprocess.run(
#         args, cwd=cwd, capture_output=capture_output, encoding="utf8"
#     )
#     if not process.returncode == 0:
#         print(process)
#
#     click.secho("..done", fg=CLICK_INFO_COLOR)
#     return process.stdout


def execute_bootstrap(install_folder: Path):
    if platform == "linux":
        executable = install_folder / "fabricator"
    else:
        executable = install_folder / "fabricator.exe"

    process = subprocess.run(
        [str(executable), "--bootstrap"], capture_output=True, encoding="utf8"
    )

    if not process.returncode == 0:
        raise FatalEchoException(process.stderr)
