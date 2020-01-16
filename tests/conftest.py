import time
from pathlib import Path
from shutil import rmtree

import pytest


# test_location = "http://localhost:8000/fabricator.ease"


def _remove(path: Path) -> bool:
    tries = 3
    current_try = 0
    if path.exists():
        while current_try < tries:
            try:
                rmtree(path)
                return True
            except Exception as err:
                time.sleep(1)
                current_try += 1

    return False


@pytest.fixture
def clean():
    yield

    _wait = False

    if _wait:
        time.sleep(1)
