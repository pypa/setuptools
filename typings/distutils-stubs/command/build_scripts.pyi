from typing import ClassVar

from _typeshed import Incomplete

from ..cmd import Command

first_line_re: Incomplete

class build_scripts(Command):
    description: str
    user_options: ClassVar[list[tuple[str, str, str]]]
    boolean_options: ClassVar[list[str]]
    build_dir: Incomplete
    scripts: Incomplete
    force: Incomplete
    executable: Incomplete
    outfiles: Incomplete
    def initialize_options(self) -> None: ...
    def finalize_options(self) -> None: ...
    def get_source_files(self): ...
    def run(self) -> None: ...
    def copy_scripts(self): ...
