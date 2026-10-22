from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

__all__ = ["DOWNLOAD_DIR", "output_file", "retrieve_file", "urls_from_file"]


NAME_REMOVE = ("http://", "https://", "github.com/", "/raw/")
DOWNLOAD_DIR = Path(__file__).parent


# ----------------------------------------------------------------------
# Please update ./preload.py accordingly when modifying this file
# ----------------------------------------------------------------------


def output_file(url: str, download_dir: Path = DOWNLOAD_DIR) -> Path:
    file_name = url.strip()
    for part in NAME_REMOVE:
        file_name = file_name.replace(part, '').strip().strip('/:').strip()
    return Path(download_dir, re.sub(r"[^\-_\.\w\d]+", "_", file_name))


def retrieve_file(
    url: str, download_dir: Path = DOWNLOAD_DIR, wait: float = 5, attempts: int = 3
) -> Path:
    path = output_file(url, download_dir)
    if path.exists():
        print(f"Skipping {url} (already exists: {path})")
        return path
    download_dir.mkdir(exist_ok=True, parents=True)
    print(f"Downloading {url} to {path}")
    last_exc: URLError | None = None
    for _ in range(attempts):
        try:
            download(url, path)
        except URLError as exc:
            # HTTPError subclasses URLError. Transient network failures
            # (e.g. ConnectionResetError, see #5284) are retried.
            last_exc = exc
            time.sleep(wait)  # wait a few seconds and try again.
        else:
            return path
    assert last_exc is not None
    raise last_exc


def urls_from_file(list_file: Path) -> list[str]:
    """``list_file`` should be a text file where each line corresponds to a URL to
    download.
    """
    print(f"file: {list_file}")
    content = list_file.read_text(encoding="utf-8")
    return [url for url in content.splitlines() if not url.startswith("#")]


def download(url: str, dest: Path):
    with urlopen(url) as f:
        data = f.read()

    with open(dest, "wb") as f:
        f.write(data)

    assert Path(dest).exists()
