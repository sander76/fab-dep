from setuptools import setup, find_packages
from fab_deploy import __version__

setup(
    name="fab-dep",
    version=__version__,
    packages=["fab_deploy"],
    install_requires=[
        "asn1crypto==0.24.0",
        "certifi==2019.3.9",
        "cffi==1.12.3",
        "chardet==3.0.4",
        "click==7.0",
        "colorama==0.4.1",
        "cryptography==2.6.1",
        "idna==2.8",
        "psutil==5.6.3",
        "pycparser==2.19",
        "pydantic==0.24",
        "requests==2.21.0",
        "six==1.12.0",
        "urllib3==1.24.2",
    ],
    url="",
    license="",
    author="Sander Teunissen",
    author_email="",
    description="",
    entry_points={"console_scripts": ["fabs=fab_deploy.cli:main"]},
)
