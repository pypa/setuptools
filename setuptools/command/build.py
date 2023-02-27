import sys
import warnings
from operator import itemgetter
from typing import TYPE_CHECKING, List, Dict
from distutils.command.build import build as _build

from setuptools import SetuptoolsDeprecationWarning
from .._importlib import metadata

if sys.version_info >= (3, 8):
    from typing import Protocol
elif TYPE_CHECKING:  # pragma: no cover
    from typing_extensions import Protocol
else:  # pragma: no cover
    from abc import ABC as Protocol


_ORIGINAL_SUBCOMMANDS = {"build_py", "build_clib", "build_ext", "build_scripts"}
_BUILD_STEPS_ENTRYPOINT = "setuptools.build_steps"


class build(_build):
    def initialize_options(self):
        super().initialize_options()
        self.sub_commands = _build.sub_commands[:]  # copy to avoid shared refs.
        self._sub_commands_loaded_from_entry_points = False

    def get_sub_commands(self):
        f"""Extends :meth:`distutils.command.build.build.get_sub_commands` to auto-load
        from ``{_BUILD_STEPS_ENTRYPOINT}`` entry-points.

        The entry-point value should be a subclass of :class:`Command`.
        If defined, the following (optional) attributes will be considered::

            priority, condition, insert_build_step

        See :doc:`userguide/extension` for more details
        """
        if not self._sub_commands_loaded_from_entry_points:
            self._verify_distutils_usage()
            self._insert_custom_steps()
            self._sub_commands_loaded_from_entry_points = True

        return super().get_sub_commands()

    def _verify_distutils_usage(self):
        subcommands = {cmd[0] for cmd in _build.sub_commands}
        if subcommands - _ORIGINAL_SUBCOMMANDS:  # pragma: no cover
            msg = """
            It seems that you are using `distutils.command.build` to add
            new subcommands. Using `distutils` directly is considered deprecated,
            please use `setuptools.command.build`.
            """
            warnings.warn(msg, SetuptoolsDeprecationWarning)
            self.sub_commands = _build.sub_commands

    def _insert_custom_steps(self):
        available = []
        for ep in metadata.entry_points(group=_BUILD_STEPS_ENTRYPOINT):
            cls = ep.load()
            cls.command_name = ep.name
            priority = getattr(cls, "priority", 0)
            available.append(((priority, ep.name), ep.name, cls))

        order = itemgetter(0)
        unique = {item[1]: item for item in sorted(available, key=order)}
        # ^-- dict insert with ASC order: removes duplicates keeping priority.

        for _, name, cls in sorted(unique.values(), key=order, reverse=True):
            # reversed sort makes sure higher priority is invoked first
            insert_fn = getattr(cls, "insert_build_step", list.append)
            condition = getattr(cls, "condition", None)
            insert_fn(self.sub_commands, (name, condition))
            self.distribution.cmdclass[name] = cls


class SubCommand(Protocol):
    """In order to support editable installations (see :pep:`660`) all
    build subcommands **SHOULD** implement this protocol. They also **MUST** inherit
    from ``setuptools.Command``.

    When creating an :pep:`editable wheel <660>`, ``setuptools`` will try to evaluate
    custom ``build`` subcommands using the following procedure:

    1. ``setuptools`` will set the ``editable_mode`` attribute to ``True``
    2. ``setuptools`` will execute the ``run()`` command.

       .. important::
          Subcommands **SHOULD** take advantage of ``editable_mode=True`` to adequate
          its behaviour or perform optimisations.

          For example, if a subcommand doesn't need to generate an extra file and
          all it does is to copy a source file into the build directory,
          ``run()`` **SHOULD** simply "early return".

          Similarly, if the subcommand creates files that would be placed alongside
          Python files in the final distribution, during an editable install
          the command **SHOULD** generate these files "in place" (i.e. write them to
          the original source directory, instead of using the build directory).
          Note that ``get_output_mapping()`` should reflect that and include mappings
          for "in place" builds accordingly.

    3. ``setuptools`` use any knowledge it can derive from the return values of
       ``get_outputs()`` and ``get_output_mapping()`` to create an editable wheel.
       When relevant ``setuptools`` **MAY** attempt to use file links based on the value
       of ``get_output_mapping()``. Alternatively, ``setuptools`` **MAY** attempt to use
       :doc:`import hooks <python:reference/import>` to redirect any attempt to import
       to the directory with the original source code and other files built in place.

    Please note that custom sub-commands **SHOULD NOT** rely on ``run()`` being
    executed (or not) to provide correct return values for ``get_outputs()``,
    ``get_output_mapping()`` or ``get_source_files()``. The ``get_*`` methods should
    work independently of ``run()``.
    """

    editable_mode: bool = False
    """Boolean flag that will be set to ``True`` when setuptools is used for an
    editable installation (see :pep:`660`).
    Implementations **SHOULD** explicitly set the default value of this attribute to
    ``False`` in ``initialize_options``.
    When subcommands run, they can use this flag to perform optimizations or change
    their behaviour accordingly.
    """

    build_lib: str
    """String representing the directory where the build artifacts should be stored,
    e.g. ``build/lib``.
    For example, if a distribution wants to provide a Python module named ``pkg.mod``,
    then a corresponding file should be written to ``{build_lib}/package/module.py``.
    A way of thinking about this is that the files saved under ``build_lib``
    would be eventually copied to one of the directories in :obj:`site.PREFIXES`
    upon installation.

    A command that produces platform-independent files (e.g. compiling text templates
    into Python functions), **CAN** initialize ``build_lib`` by copying its value from
    the ``build_py`` command. On the other hand, a command that produces
    platform-specific files **CAN** initialize ``build_lib`` by copying its value from
    the ``build_ext`` command. In general this is done inside the ``finalize_options``
    method with the help of the ``set_undefined_options`` command::

        def finalize_options(self):
            self.set_undefined_options("build_py", ("build_lib", "build_lib"))
            ...
    """

    def initialize_options(self):
        """(Required by the original :class:`setuptools.Command` interface)"""

    def finalize_options(self):
        """(Required by the original :class:`setuptools.Command` interface)"""

    def run(self):
        """(Required by the original :class:`setuptools.Command` interface)"""

    def get_source_files(self) -> List[str]:
        """
        Return a list of all files that are used by the command to create the expected
        outputs.
        For example, if your build command transpiles Java files into Python, you should
        list here all the Java files.
        The primary purpose of this function is to help populating the ``sdist``
        with all the files necessary to build the distribution.
        All files should be strings relative to the project root directory.
        """

    def get_outputs(self) -> List[str]:
        """
        Return a list of files intended for distribution as they would have been
        produced by the build.
        These files should be strings in the form of
        ``"{build_lib}/destination/file/path"``.

        .. note::
           The return value of ``get_output()`` should include all files used as keys
           in ``get_output_mapping()`` plus files that are generated during the build
           and don't correspond to any source file already present in the project.
        """

    def get_output_mapping(self) -> Dict[str, str]:
        """
        Return a mapping between destination files as they would be produced by the
        build (dict keys) into the respective existing (source) files (dict values).
        Existing (source) files should be represented as strings relative to the project
        root directory.
        Destination files should be strings in the form of
        ``"{build_lib}/destination/file/path"``.
        """
