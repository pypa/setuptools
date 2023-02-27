import os
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

from setuptools import Command
from setuptools.dist import Distribution
from setuptools._importlib import metadata


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


class StepPrepend(Cmd):
    @staticmethod
    def insert_build_step(steps, entry):
        steps.insert(0, entry)

    def run(self):
        assert not Path(self.distribution.src_root, "step-append.run").exists()
        Path(self.distribution.src_root, "step-prepend.run").touch()


class StepSuperseded(Cmd):
    def run(self):
        Path(self.distribution.src_root, "step-superseded.run").touch()
        raise AssertionError("Should not have been called")


class StepAppend(Cmd):
    priority = 100
    # Append by default, no need for insert_build_step

    def run(self):
        assert Path(self.distribution.src_root, "step-prepend.run").exists()
        Path(self.distribution.src_root, "step-append.run").touch()


def test_custom_build_sub_commands(monkeypatch, tmp_path):
    with replace_entry_points(
        monkeypatch,
        "setuptools.build_steps",
        [
            ("step_append", StepAppend),
            ("step_append", StepSuperseded),
            ("step_prepend", StepPrepend),
        ]
    ):
        attrs = {**BASE_DIST_EXAMPLE, "src_root": str(tmp_path)}
        dist = Distribution(attrs)
        build = dist.get_command_obj("build")
        sub_cmds = tuple(build.get_sub_commands())

        # Make sure ``after`` and ``before`` result in correct order
        assert sub_cmds[0] == "step_prepend"
        assert sub_cmds[-1] == "step_append"

        # Make sure sub command classes are registered
        assert dist.get_command_class("step_prepend") == StepPrepend
        assert dist.get_command_class("step_append") == StepAppend

        # Make sure commands run correctly
        here = os.getcwd()
        try:
            os.chdir(tmp_path)
            dist.run_command("build")
        finally:
            os.chdir(here)

        assert (tmp_path / "step-prepend.run").exists()
        assert (tmp_path / "step-append.run").exists()
        assert not (tmp_path / "step-superseded.run").exists()


@contextmanager
def replace_entry_points(monkeypatch, replaced_group, values):
    """Replace an specific entry-point group in importlib.metadata"""
    eps = []
    for name, cls in values:
        ep = Mock()
        ep.name = name
        ep.load = Mock(return_value=cls)
        eps.append(ep)

    orig = metadata.entry_points

    def replacement(*args, **kwargs):
        group = kwargs.get("group", None)
        if group == replaced_group:
            return iter(eps)
        return orig(*args, **kwargs)

    with monkeypatch.context() as m:
        m.setattr(metadata, "entry_points", replacement)
        yield
