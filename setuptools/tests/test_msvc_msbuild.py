"""Tests for the MSBuild property of EnvironmentInfo (issue #5275)."""

import os

import pytest

from ..msvc import EnvironmentInfo


class FakePlatformInfo:
    def current_dir(self, hidex86=False):
        return '' if hidex86 else '\\x86'


class FakeRegistryInfo:
    def __init__(self, pi, vs_install_dir=None):
        self.pi = pi
        self._vs_install_dir = vs_install_dir
        self.vs = 'vs'

    def lookup(self, key, version):
        return self._vs_install_dir


def make_env(
    monkeypatch,
    tmp_path,
    vs_ver,
    vs_install_dir=None,
    known_vs_paths=None,
    program_filesx86='C:\\Program Files (x86)',
):
    """Build an EnvironmentInfo whose filesystem view is rooted at tmp_path."""

    real_isdir = os.path.isdir

    def fake_isdir(path):
        path = str(path)
        if path.startswith('C:\\'):
            # Translate synthetic absolute paths into the temp tree.
            rel = path[3:]
            return real_isdir(os.path.join(tmp_path, rel))
        return real_isdir(path)

    env = object.__new__(EnvironmentInfo)
    fake_si = type('SI', (), {})()
    fake_si.vs_ver = vs_ver
    fake_si.ProgramFilesx86 = program_filesx86
    fake_si.VSInstallDir = (
        vs_install_dir
        if vs_install_dir is not None
        else os.path.join(
            program_filesx86, f'Microsoft Visual Studio {vs_ver:0.1f}'
        )
    )
    env.si = fake_si
    env.known_vs_paths = dict(known_vs_paths or {})
    env.ri = FakeRegistryInfo(FakePlatformInfo())
    env.pi = env.ri.pi
    monkeypatch.setattr(os.path, 'isdir', fake_isdir)
    return env


class TestMSBuildProperty:
    def test_vs2019_and_later_use_current_layout(self, monkeypatch, tmp_path):
        """VS2019+ (v16+) must use the version-independent Current layout."""
        env = make_env(monkeypatch, tmp_path, 16.0)
        paths = env.MSBuild
        assert paths == [
            os.path.join(env.si.VSInstallDir, r'MSBuild\Current\bin'),
            os.path.join(env.si.VSInstallDir, r'MSBuild\Current\bin', 'Roslyn'),
        ]

    def test_vs2022_multiline_version_gets_current_layout(
        self, monkeypatch, tmp_path
    ):
        """Regression for #5275: vs_ver like 17.12/18.7 must not fall back to a
        per-version directory that never exists on VS2019+ installs."""
        env = make_env(monkeypatch, tmp_path, 17.12)
        paths = env.MSBuild
        assert all(r'MSBuild\17.1\bin' not in p for p in paths)
        assert any(r'MSBuild\Current\bin' in p for p in paths)

    def test_vs2026_uses_current_layout(self, monkeypatch, tmp_path):
        env = make_env(monkeypatch, tmp_path, 18.7)
        paths = env.MSBuild
        assert any(r'MSBuild\Current\bin' in p for p in paths)
        assert not any(r'MSBuild\18.' in p for p in paths)

    def test_vs2015_keeps_legacy_layout(self, monkeypatch, tmp_path):
        """VS2015 and earlier keep the historical per-version layout."""
        env = make_env(monkeypatch, tmp_path, 14.0)
        paths = env.MSBuild
        assert paths == [
            os.path.join('C:\\Program Files (x86)', r'MSBuild\14.0\bin')
        ]

    def test_vs2017_keeps_per_version_layout(self, monkeypatch, tmp_path):
        """VS2017 (15.x) keeps the per-version layout under VSInstallDir."""
        env = make_env(monkeypatch, tmp_path, 15.9)
        paths = env.MSBuild
        assert [p for p in paths if not p.endswith('\\Roslyn')] == [
            os.path.join(env.si.VSInstallDir, r'MSBuild\15.9\bin')
        ]

    def test_too_old_returns_empty(self, monkeypatch, tmp_path):
        env = make_env(monkeypatch, tmp_path, 11.0)
        assert env.MSBuild == []

    def test_nonexistent_candidates_are_filtered_only_if_alternatives_exist(
        self, monkeypatch, tmp_path
    ):
        """When no candidate directory exists on disk, the raw candidates are
        returned unchanged; when Current exists it wins and Roslyn follows."""
        current_bin = tmp_path / r'MSBuild\Current\bin'
        current_bin.mkdir(parents=True)

        env = make_env(monkeypatch, tmp_path, 17.12, vs_install_dir='C:\\VS')
        paths = env.MSBuild
        assert paths == [
            'C:\\VS\\MSBuild\\Current\\bin',
            'C:\\VS\\MSBuild\\Current\\bin\\Roslyn',
        ]

        # Nothing exists -> unfiltered candidates are returned.
        current_bin.rmdir()
        env2 = make_env(monkeypatch, tmp_path, 17.12, vs_install_dir='C:\\VS')
        assert env2.MSBuild == [
            'C:\\VS\\MSBuild\\Current\\bin',
            'C:\\VS\\MSBuild\\Current\\bin\\Roslyn',
        ]

    @pytest.mark.skipif(os.name != 'nt', reason="Windows-only behaviour")
    def test_real_environment_returns_existing_paths(self):
        """On a machine with a real VS install, every returned path exists."""
        try:
            env = EnvironmentInfo('amd64')
        except Exception:
            pytest.skip("No MSVC installation detected")
        if env.vs_ver < 15.0:
            pytest.skip("Legacy VS layout installed")
        for path in env.MSBuild:
            assert os.path.isdir(path), f"Nonexistent MSBuild path: {path}"
