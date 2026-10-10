from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

from . import output_file, retrieve_file


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def _patch_urlopen(side_effect):
    return patch("setuptools.tests.config.downloads.urlopen", side_effect=side_effect)


def test_download_first_try(tmp_path):
    with _patch_urlopen(lambda url: FakeResponse(b"data")):
        path = retrieve_file("https://example.com/pkg/setup.cfg", tmp_path, wait=0)
    assert path.read_bytes() == b"data"


def test_transient_urlerror_is_retried(tmp_path):
    # https://github.com/pypa/setuptools/issues/5284 — ConnectionResetError
    # escaped unretried because only HTTPError was caught.
    calls = []

    def flaky(url):
        calls.append(url)
        if len(calls) == 1:
            raise URLError(ConnectionResetError(104, "Connection reset by peer"))
        return FakeResponse(b"data")

    with _patch_urlopen(flaky):
        path = retrieve_file("https://example.com/pkg/setup.cfg", tmp_path, wait=0)
    assert path.read_bytes() == b"data"
    assert len(calls) == 2


def test_transient_httperror_is_retried(tmp_path):
    calls = []

    def flaky(url):
        calls.append(url)
        if len(calls) == 1:
            raise HTTPError(url, 503, "Service Unavailable", {}, None)
        return FakeResponse(b"data")

    with _patch_urlopen(flaky):
        path = retrieve_file("https://example.com/pkg/setup.cfg", tmp_path, wait=0)
    assert path.read_bytes() == b"data"
    assert len(calls) == 2


def test_persistent_failure_raises_after_attempts(tmp_path):
    calls = []

    def dead(url):
        calls.append(url)
        raise URLError(ConnectionResetError(104, "Connection reset by peer"))

    with _patch_urlopen(dead), pytest.raises(URLError):
        retrieve_file("https://example.com/pkg/setup.cfg", tmp_path, wait=0, attempts=3)
    assert len(calls) == 3


def test_cached_file_skips_download(tmp_path):
    url = "https://example.com/pkg/setup.cfg"
    output_file(url, tmp_path).write_bytes(b"cached")

    def fail(url):
        raise AssertionError("urlopen should not be called for cached files")

    with _patch_urlopen(fail):
        path = retrieve_file(url, tmp_path, wait=0)
    assert path.read_bytes() == b"cached"
