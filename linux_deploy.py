import logging
import shutil
from pathlib import Path
import os
import subprocess

# from subprocess import PIPE, Popen

_LOGGER = logging.getLogger(__name__)

from fab_deploy import __version__

app_folder = Path("/app/fab-dep/")

package_folder = Path("/app/fab/usr/")
bin_folder = package_folder / "bin"


package_config_folder = Path("/app/fab/DEBIAN")


def make_control_file():
    """Make a control file which allows for deb file installers."""

    _LOGGER = logging.getLogger(__name__)

    dct = {
        "Package": "fab",
        "Version": __version__,
        "Section": "custom",
        "Priority": "optional",
        "Architecture": "amd64",
        "Essential": "no",
        "Maintainer": "s.teunissen",
        "Description": "fabrication update tool",
    }

    contents = "\n".join("{}: {}".format(key, value) for key, value in dct.items())

    with open(package_config_folder.joinpath("control"), "w") as fl:
        fl.write(contents)
        fl.write("\n")


def _run(*args, cwd=app_folder, capture_output=True):
    process = subprocess.run(
        args, cwd=cwd, capture_output=capture_output, encoding="utf8"
    )
    print(process)

    return process.stdout


def deploy_linux():

    shutil.rmtree(bin_folder, ignore_errors=True)
    shutil.rmtree(package_config_folder, ignore_errors=True)

    package_config_folder.mkdir(exist_ok=True, parents=True)
    # package_folder.mkdir(exist_ok=True,parents=True)

    _run("git", "pull")

    content = _run("pipenv", "lock", "-r")
    with open(app_folder / "reqs.txt", "w") as fl:
        fl.write(content)

    content = _run("pipenv", "lock", "-r", "-d")
    with open(app_folder / "reqs-dev.txt", "w") as fl:
        fl.write(content)

    _run("python3.7", "-m", "pip", "install", "-r", "reqs.txt")

    _run("python3.7", "-m", "pip", "install", "-r", "reqs-dev.txt")

    _run("pyinstaller", "fab.spec")

    make_control_file()

    shutil.copytree(app_folder.joinpath("dist", "fab"), bin_folder)

    _run("dpkg-deb", "--build", "fab", cwd=Path("/app/"))


if __name__ == "__main__":
    deploy_linux()
