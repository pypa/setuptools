import re
from pathlib import Path
from urllib.request import urlopen
from unittest.mock import Mock

import pytest

from setuptools import config
from setuptools.config import expand


EXAMPLES = (Path(__file__).parent / "setupcfg_examples.txt").read_text()
EXAMPLE_URLS = [x for x in EXAMPLES.splitlines() if not x.startswith("#")]
DOWNLOAD_DIR = Path(__file__).parent / "downloads"


@pytest.mark.parametrize("url", EXAMPLE_URLS)
@pytest.mark.filterwarnings("ignore")
def test_succesfull_conversion(url, monkeypatch):
    monkeypatch.setattr(expand, 'read_attr', Mock(return_value="0.0.1"))
    example = retrieve_file(url, DOWNLOAD_DIR)
    config.read(example, syntax="ini")


NAME_REMOVE = ("http://", "https://", "github.com/", "/raw/")


def retrieve_file(url, download_dir):
    file_name = url.strip()
    for part in NAME_REMOVE:
        file_name = file_name.replace(part, '').strip().strip('/:').strip()
    file_name = re.sub(r"[^\-_\.\w\d]+", "_", file_name)
    path = Path(download_dir, file_name)
    if not path.exists():
        download_dir.mkdir(exist_ok=True, parents=True)
        download(url, path)
    return path


def download(url, dest):
    with urlopen(url) as f:
        data = f.read()

    with open(dest, "wb") as f:
        f.write(data)

    assert Path(dest).exists()
