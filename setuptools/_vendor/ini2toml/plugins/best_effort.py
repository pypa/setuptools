import re
from functools import partial
from typing import TypeVar

from ..transformations import split_comment, split_kv_pairs, split_list, split_scalar
from ..types import HiddenKey, IntermediateRepr, Translator

M = TypeVar("M", bound=IntermediateRepr)

SECTION_SPLITTER = re.compile(r"\.|:|\\")
KEY_SEP = "="


def activate(translator: Translator):
    profile = translator["best_effort"]
    plugin = BestEffort()
    profile.intermediate_processors.append(plugin.process_values)
    profile.help_text = plugin.__doc__ or ""


class BestEffort:
    """Guess option value conversion based on the string format"""

    def __init__(
        self,
        key_sep=KEY_SEP,
        section_splitter=SECTION_SPLITTER,
    ):
        self.key_sep = key_sep
        self.section_splitter = section_splitter
        self.split_dict = partial(split_kv_pairs, key_sep=KEY_SEP)

    def process_values(self, doc: M) -> M:
        doc_items = list(doc.items())
        for name, section in doc_items:
            doc[name] = self.apply_best_effort_to_section(section)
            # Separate nested sections
            if self.section_splitter.search(name):
                keys = tuple(self.section_splitter.split(name))
                doc.rename(name, keys)
        return doc

    def apply_best_effort_to_section(self, section: M) -> M:
        options = list(section.items())
        # Convert option values:
        for field, value in options:
            self.apply_best_effort(section, field, value)
        return section

    def apply_best_effort(self, container: M, field: str, value: str):
        if isinstance(field, HiddenKey):
            return
        lines = value.splitlines()
        if len(lines) > 1:
            if self.key_sep in value:
                container[field] = self.split_dict(value)
            else:
                container[field] = split_list(value)
        elif field.endswith("version"):
            container[field] = split_comment(value)
        else:
            container[field] = split_scalar(value)
