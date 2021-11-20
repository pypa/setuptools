import os
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import pkg_resources
from setuptools import Command
from setuptools.dist import Distribution


BASE_DIST_EXAMPLE = {
    "script_name": "setup.py",
    "script_args": ["build"],
    "packages": [""],
    "name": "example",
    "version": "0.0.1",
}


class Cmd(Command):
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class Step0(Cmd):
    before = "build_py"

    def run(self):
        assert not Path(self.distribution.src_root, "step1.run").exists()
        Path(self.distribution.src_root, "step0.run").touch()


class Step1(Cmd):
    after = "step0"

    def run(self):
        assert Path(self.distribution.src_root, "step0.run").exists()
        Path(self.distribution.src_root, "step1.run").touch()


class Step2(Cmd):
    # no after or before => last sub command

    def run(self):
        assert Path(self.distribution.src_root, "step0.run").exists()
        assert Path(self.distribution.src_root, "step1.run").exists()
        Path(self.distribution.src_root, "step2.run").touch()


def test_custom_build_sub_commands(monkeypatch, tmp_path):
    with replace_entry_points(
        monkeypatch,
        "setuptools.sub_commands.build",
        {"step0": Step0, "step1": Step1, "step2": Step2}
    ):
        attrs = {**BASE_DIST_EXAMPLE, "src_root": str(tmp_path)}
        dist = Distribution(attrs)
        build = dist.get_command_obj("build")
        sub_cmds = tuple(build.get_sub_commands())

        # Make sure ``after`` and ``before`` result in correct order
        assert sub_cmds[0] == "step0"
        assert sub_cmds[1] == "step1"
        assert sub_cmds[-1] == "step2"

        # Make sure sub command classes are registered
        assert dist.get_command_class("step0") == Step0
        assert dist.get_command_class("step1") == Step1
        assert dist.get_command_class("step2") == Step2

        # Make sure commands run correctly
        here = os.getcwd()
        try:
            os.chdir(tmp_path)
            dist.run_command("build")
        finally:
            os.chdir(here)

        assert (tmp_path / "step0.run").exists()
        assert (tmp_path / "step1.run").exists()
        assert (tmp_path / "step2.run").exists()


@contextmanager
def replace_entry_points(monkeypatch, replaced_group, values):
    """Replace an specific entry-point group in pkg_resources"""
    eps = []
    for name, cls in values.items():
        ep = Mock()
        ep.name = name
        ep.load = Mock(return_value=cls)
        eps.append(ep)

    orig = pkg_resources.iter_entry_points

    def replacement(group, name=None):
        if group == replaced_group:
            return iter(eps)
        return orig(group, name)

    with monkeypatch.context() as m:
        m.setattr(pkg_resources, "iter_entry_points", replacement)
        yield
