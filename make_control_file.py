"""Make a control file which allows for deb file installers."""

import logging

from fab_deploy import __version__

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


def make_version_file():
    contents = "\n".join("{}: {}".format(key, value) for key, value in dct.items())

    with open("/app/fab/DEBIAN/control", "W") as fl:
        fl.write(contents)


if __name__ == "__main__":
    make_version_file()
