from typing import ClassVar, Final

from _typeshed import Incomplete
from docutils.utils import Reporter

from ..cmd import Command

class SilentReporter(Reporter):
    messages: Incomplete
    def __init__(
        self,
        source,
        report_level,
        halt_level,
        stream: Incomplete | None = ...,
        debug: bool = False,
        encoding: str = ...,
        error_handler: str = ...,
    ) -> None: ...
    def system_message(self, level, message, *children, **kwargs): ...

HAS_DOCUTILS: Final[bool]

class check(Command):
    description: str
    user_options: ClassVar[list[tuple[str, str, str]]]
    boolean_options: ClassVar[list[str]]
    restructuredtext: int
    metadata: int
    strict: int
    def initialize_options(self) -> None: ...
    def finalize_options(self) -> None: ...
    def warn(self, msg): ...
    def run(self) -> None: ...
    def check_metadata(self) -> None: ...
    def check_restructuredtext(self) -> None: ...
