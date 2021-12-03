import logging
import re
import warnings
from functools import partial, reduce
from itertools import chain, zip_longest
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

try:
    from packaging.requirements import Requirement
except ImportError:  # pragma: no cover
    from setuptools.extern.packaging.requirements import Requirement  # type: ignore

from ..transformations import (
    apply,
    coerce_bool,
    deprecated,
    kebab_case,
    noop,
    split_comment,
    split_kv_pairs,
    split_list,
)
from ..types import Commented, CommentedKV, CommentedList, CommentKey, HiddenKey
from ..types import IntermediateRepr as IR
from ..types import Transformation, Translator, WhitespaceKey
from .best_effort import BestEffort

try:
    from setuptools._distutils import command as distutils_commands
except ImportError:  # pragma: no cover
    from distutils import command as distutils_commands

R = TypeVar("R", bound=IR)

RenameRules = Dict[Tuple[str, ...], Union[Tuple[Union[str, int], ...], None]]
ProcessingRules = Dict[Tuple[str, ...], Transformation]


_logger = logging.getLogger(__name__)

chain_iter = chain.from_iterable

# Functions that split values from comments and parse those values
split_list_comma = partial(split_list, sep=",", subsplit_dangling=False)
split_list_semi = partial(split_list, sep=";", subsplit_dangling=False)
split_hash_comment = partial(split_comment, comment_prefixes="#")  # avoid splitting `;`
split_bool = partial(split_comment, coerce_fn=coerce_bool)
split_kv_of_lists = partial(split_kv_pairs, coerce_fn=split_list_comma)
# URLs can contain the # symbol
split_kv_urls = partial(split_kv_pairs, comment_prefixes=(" #",))
split_url = partial(split_comment, comment_prefixes=(" #",))

SECTION_SPLITTER = re.compile(r"\.|:")
SETUPTOOLS_SECTIONS = ("metadata", "options")
SKIP_CHILD_NORMALISATION = (
    "options.entry_points",
    "options.package_data",
    "options.exclude_package_data",
    "options.extras_require",
    "options.data_files",
)
COMMAND_SECTIONS = (
    "global",
    "alias",
    "install",
    "develop",
    "sdist",
    "bdist",
    "bdist_wheel",
    *getattr(distutils_commands, "__all__", []),
)
DEFAULT_LICENSE_FILES = ("LICEN[CS]E*", "COPYING*", "NOTICE*", "AUTHORS*")
# defaults from the `wheel` package


def activate(translator: Translator):
    plugin = SetuptoolsPEP621()
    profile = translator["setup.cfg"]
    profile.intermediate_processors += [plugin.normalise_keys, plugin.pep621_transform]
    profile.help_text = plugin.__doc__ or ""


class SetuptoolsPEP621:
    """Convert settings to 'pyproject.toml' based on :pep:`621`"""

    BUILD_REQUIRES = ("setuptools", "wheel")

    def __init__(self):
        self._be = BestEffort(key_sep="=")

    @classmethod
    def template(
        cls,
        ir_cls: Type[R] = IR,  # type: ignore
        build_requires: Sequence[str] = (),
    ) -> R:
        build_system = {
            "requires": [*(build_requires or cls.BUILD_REQUIRES)],
            # ^ NOTE: the code ahead assumes no version
            "build-backend": "setuptools.build_meta",
        }
        tpl = {
            "metadata": ir_cls(),  # NOTE: will be renamed later
            "build-system": ir_cls(build_system),  # type: ignore
            "tool": ir_cls(),
        }
        return ir_cls(tpl)  # type: ignore

    def setupcfg_aliases(self):
        """``setup.cfg`` aliases as defined in:
        https://setuptools.pypa.io/en/stable/userguide/declarative_config.html
        """
        return {
            "classifier": "classifiers",
            "summary": "description",
            "platform": "platforms",
            "license-file": "license-files",
            "home-page": "url",
        }

    def processing_rules(self) -> ProcessingRules:
        """Value type processing, as defined in:
        https://setuptools.pypa.io/en/stable/userguide/declarative_config.html
        """
        # If not present bellow will be transformed via split_comment by default
        return {
            ("metadata", "version"): directive("file", "attr"),
            ("metadata", "classifiers"): directive("file", orelse=split_list_comma),
            ("metadata", "keywords"): split_list_comma,
            ("metadata", "description"): directive("file"),
            # ---
            ("metadata", "long-description"): directive("file", orelse=noop),
            ("metadata", "long-description-content-type"): split_hash_comment,
            # => NOTICE: further processed via
            #            `merge_and_rename_long_description_and_content_type`
            # ---
            ("metadata", "license-files"): split_list_comma,
            # => NOTICE: in PEP 621, it should be a single file
            #            further processed via `handle_license_and_files`
            # ---
            ("metadata", "url"): split_url,
            ("metadata", "download-url"): split_url,
            ("metadata", "project-urls"): split_kv_urls,
            # => NOTICE: further processed via `merge_and_rename_urls`
            # ---- Not covered by PEP 621 ----
            ("metadata", "platforms"): split_list_comma,
            # ---
            ("metadata", "provides"): split_list_comma,
            ("metadata", "requires"): deprecated("requires", split_list_comma),
            ("metadata", "obsoletes"): split_list_comma,
            # => NOTICE: not supported by pip
            # ---- Options ----
            ("options", "zip-safe"): split_bool,
            ("options", "setup-requires"): split_deps,
            ("options", "install-requires"): split_deps,
            ("options", "tests-require"): split_deps,
            ("options", "scripts"): split_list_comma,
            ("options", "eager-resources"): split_list_comma,
            ("options", "dependency-links"): deprecated(
                "dependency-links", split_list_comma
            ),  # noqa
            ("options", "entry-points"): directive(
                "file", orelse=value_error("option.entry-points")
            ),
            ("options", "include-package-data"): split_bool,
            ("options", "package-dir"): split_kv_pairs,
            ("options", "namespace-packages"): split_list_comma,
            ("options", "py-modules"): split_list_comma,
            ("options", "cmdclass"): split_kv_pairs,
            ("options", "data-files"): deprecated("data-files", split_kv_of_lists),
            ("options", "packages"): directive(
                "find", "find_namespace", orelse=split_list_comma
            ),
            ("options.packages.find", "include"): split_list_comma,
            ("options.packages.find", "exclude"): split_list_comma,
            ("options.packages.find", "exclude"): split_list_comma,
        }
        # See also dependent_processing_rules

    def dependent_processing_rules(self, doc: IR) -> ProcessingRules:
        """Dynamically create processing rules, such as :func:`processing_rules` based
        on the existing document.
        """
        groups: Mapping[str, Transformation] = {
            "options.extras-require": split_deps,
            "options.package-data": split_list_comma,
            "options.exclude-package-data": split_list_comma,
            "options.data-files": split_list_comma,
            "options.entry-points": split_kv_pairs,
        }
        return {
            (g, k): fn
            for g, fn in groups.items()
            for k in doc.get(g, ())
            if isinstance(k, str)
        }

    def apply_value_processing(self, doc: R) -> R:
        """Process ``setup.cfg`` values according to :meth:`processing_rules` and
        :meth:`dependent_processing_rules`.

        This function assumes all field names were normalised by :meth:`normalise_keys`.
        """
        default = {
            (name, option): split_comment
            for name, section in doc.items()
            if name in ("metadata", "options")
            for option in section
            if isinstance(option, (str, tuple)) and not isinstance(option, HiddenKey)
        }
        transformations: dict = {
            **default,
            **self.processing_rules(),
            **self.dependent_processing_rules(doc),
        }
        for (section, option), fn in transformations.items():
            value = doc.get(section, {}).get(option, None)
            if value is not None:
                doc[section][option] = fn(value)
        return doc

    def merge_and_rename_urls(self, doc: R) -> R:
        """The following renames can be applied when comparing setuptools metadata and
        :pep:`621`::

            url => urls.homepage
            download-url => urls.download
            project-urls.* => urls.*
        """
        metadata: IR = doc["metadata"]
        new_urls = [
            (dest, metadata.pop(orig))
            for orig, dest in [("url", "Homepage"), ("download-url", "Download")]
            if orig in metadata
        ]
        urls = metadata.get("project-urls", CommentedKV())
        for k, v in reversed(new_urls):
            urls.insert_line(0, [(k, v.value)], v.comment)

        if urls.as_dict():
            keys = ("project-urls", "url", "download-url")
            metadata.replace_first_remove_others(keys, "urls", urls)
        return doc

    def merge_authors_maintainers_and_emails(self, doc: R) -> R:
        """When transforming setuptools metadata and :pep:`621`, we have to merge
        ``author/maintainer`` and ``author-email/maintainer-email`` into a single
        dict-like object with 2 keys.
        Some projects also provide multiple, comma separated, values for each field.
        In that case we assume that the value for the i-th author/maintainer should be
        paired with to the i-th author-email/maintainer-email value.
        """
        metadata: IR = doc["metadata"]

        def _split_values(field):
            commented: Commented[str] = metadata.get(field, Commented())
            values = commented.value_or("").strip().split(",")
            return (v.strip() for v in values), commented.comment

        for key in ("author", "maintainer"):
            fields = (key, f"{key}-email")
            values, comments = zip(*(_split_values(f) for f in fields))
            combined = (
                {k: v for k, v in zip(("name", "email"), person_data) if v}
                # ^-- Remove empty fields
                for person_data in zip_longest(*values, fillvalue="")
            )
            people = [IR(c) for c in combined if c]  # type: ignore[arg-type]

            if people:
                # author/maintainer => author**S**/maintainer**S**
                i = metadata.replace_first_remove_others(fields, f"{key}s", people)
                for j, cmt in enumerate(c for c in comments if c):
                    metadata.insert(j + i + 1, CommentKey(), cmt)
        return doc

    def merge_and_rename_long_description_and_content_type(self, doc: R) -> R:
        """:pep:`621` offers a single field (``readme``) to cover things present in two
        fields in ``setup.cfg``::

            long_description.file => readme.file
            long_description => readme.text
            long-description-content-type => readme.content-type

        We also have to be aware that :pep:`621` accepts a single file, so the option of
        combining multiple files as presented in ``setup.cfg`` have to be handled via
        ``dynamic``.
        """
        metadata: IR = doc["metadata"]
        long_desc: Union[Directive, str, None] = metadata.get("long-description")
        if not long_desc:
            metadata.pop("long-description", None)
            metadata.pop("long-description-content-type", None)
            return doc

        readme: Dict[str, Any] = {}
        dynamic = False
        if isinstance(long_desc, Directive):
            # In PEP 621 "readme" should be a single file
            files: CommentedList[str] = long_desc["file"]
            files_list = files.as_list()
            if len(files_list) == 1:
                readme = {"file": Commented(files_list[0], files[0].comment)}
            else:
                readme = dict(long_desc)
                dynamic = True
        else:
            readme = {"text": long_desc.strip()}

        content_type = metadata.pop("long-description-content-type", None)
        if content_type:
            readme["content-type"] = content_type

        if dynamic:
            metadata.setdefault("dynamic", []).append("readme")
            doc.setdefault("options.dynamic", IR()).append("readme", readme)
            metadata.pop("long-description")
            return doc

        if len(list(readme.keys())) == 1 and "file" in readme:
            metadata["long-description"] = readme["file"]
        else:
            metadata["long-description"] = IR(readme)  # type: ignore[arg-type]
        metadata.rename("long-description", "readme")
        return doc

    def handle_license_and_files(self, doc: R) -> R:
        """In :pep:`621` we have a single field for license, which might have a single
        value (file path) or a dict-like structure::

            license-files => license.file
            license => license.text

        We also have to be aware that :pep:`621` accepts a single file, so the option of
        combining multiple files as presented in ``setup.cfg`` have to be handled via
        ``dynamic``.
        """
        metadata: IR = doc["metadata"]
        files: Optional[CommentedList[str]] = metadata.get("license-files")
        # Setuptools automatically includes license files if not present
        # so let's make it dynamic
        files_as_list = (files and files.as_list()) or list(DEFAULT_LICENSE_FILES)
        text = metadata.get("license")

        # PEP 621 specifies a single "file". If there is more, we need to use "dynamic"
        if files_as_list and (
            len(files_as_list) > 1
            or any(char in files_as_list[0] for char in "*?[")  # glob pattern
            or text  # PEP 621 forbids both license and license-files at the same time
        ):
            metadata.setdefault("dynamic", []).append("license")
            dynamic = doc.setdefault("options.dynamic", IR())
            if text:
                dynamic.append("license", text)
            dynamic.append("license-files", files_as_list)
            # 'file' and 'text' are mutually exclusive in PEP 621
            metadata.pop("license", None)
            metadata.pop("license-files", None)
            return doc

        if files_as_list:
            files = cast(CommentedList[str], files)
            license = IR(file=Commented(files_as_list[0], files[0].comment))
        elif text:
            license = IR(text=metadata["license"])
        else:
            return doc

        fields = ("license-files", "license")
        metadata.replace_first_remove_others(fields, "license", license)
        return doc

    def move_and_split_entrypoints(self, doc: R) -> R:
        """In ``setup.cfg`` there is no special treatment for entry-points that will be
        transformed in console/GUI scripts. On the other hand :pep:`621` defines
        separated fields::

            entry-points.console-scripts => scripts
            entry-points.gui-scripts => gui-scripts
            entry-points.* => "entry-points".*
        """
        entrypoints: IR = doc.get("options.entry-points", IR())
        if not entrypoints:
            doc.pop("options.entry-points", None)
            return doc
        doc.rename("options.entry-points", "project:entry-points")
        # ^ use `:` to guarantee it is split later
        script_keys = ["console-scripts", "gui-scripts"]
        script_keys += [k.replace("-", "_") for k in script_keys]
        keys = (k for k in script_keys if k in entrypoints)
        for key in keys:
            scripts: CommentedKV = entrypoints.pop(key)
            new_key = key.replace("_", "-").replace("console-", "")
            doc.append(f"project:{new_key}", scripts.to_ir())
        if not entrypoints or all(isinstance(k, WhitespaceKey) for k in entrypoints):
            doc.pop("project:entry-points")
        return doc

    def move_options_missing_in_pep621(self, doc: R) -> R:
        """:pep:`621` specifies as project metadata values that are covered
        in ``setup.cfg "options"`` section.
        """
        # First we handle simple options
        naming = {
            "python-requires": "requires-python",
            "install-requires": "dependencies",
            "entry-points": "entry-points",
        }
        metadata = doc.setdefault("metadata", IR())
        options = doc.setdefault("options", IR())
        metadata.update({v: options.pop(k) for k, v in naming.items() if k in options})

        # Then we handle entire sections:
        naming = {"extras-require": "optional-dependencies"}
        for src, target in naming.items():
            doc.rename(f"options.{src}", f"project:{target}", ignore_missing=True)

        return doc

    def remove_metadata_not_in_pep621(self, doc: R) -> R:
        """:pep:`621` does not cover all project metadata in ``setup.cfg "metadata"``
        section. That is left as "tool" specific configuration.
        """
        specific = ["platforms", "provides", "obsoletes"]
        metadata, options = doc["metadata"], doc["options"]
        options.update({k: metadata.pop(k) for k in specific if k in metadata})
        return doc

    def rename_script_files(self, doc: R) -> R:
        """``setuptools`` define a ``options.scripts`` parameters that refer to
        script files, not created via entry-points.
        To avoid confusion with :pep:`621` scripts (generated via entry-points)
        let's rename this field to ``script-files``
        """
        doc["options"].rename("scripts", "script-files", ignore_missing=True)
        return doc

    def handle_packages_find(self, doc: R) -> R:
        """``setup.cfg`` uses a option + a section to define ``options.packages.find``
        and its ``find_namespace`` variant. This does not work very well with the
        convention used for the TOML encoding, since the option and the section would
        end up with the same name (and overwriting each other). Therefore we need to
        "merge" them.
        """
        options = doc["options"]
        # Abort when not using find or find_namespace
        packages = options.get("packages")
        if not isinstance(packages, Directive):
            return doc
        prefix = packages.kind.replace("_", "-")
        # Enhancement #1: Unify find and find_namespaces, using `namespaces` as a flag
        options["packages"] = Directive("find", {"namespaces": "namespace" in prefix})
        if "options.packages.find" in doc:
            packages = options.pop("packages")
            doc["options.packages.find"].update(packages["find"])
            # Enhancement #2: ``where`` accepts multiple values (array)
            where = doc["options.packages.find"].get("where", None)
            if where:
                doc["options.packages.find"]["where"] = _ensure_where_list(where)
        return doc

    def handle_dynamic(self, doc: R) -> R:
        """All the configuration fields in :pep:`621` that are dynamically discovered at
        build time have to be explicitly list in ``dynamic``.
        This function moves directive usages (e.g. ``file:`` and ``attr:``) to a
        tool-specific subtable (``tool.setuptools.dynamic``), and add the corresponding
        field to ``dynamic``.
        Since ``version`` is a mandatory core metadata, it will be added to ``dynamic``
        when not explicitly set (in that case plugins such as ``setuptools_scm`` are
        expected to provide a value at runtime).
        """
        potential = ["version", "classifiers", "description"]
        # directives = {k[-1]: v for k, v in self.setupcfg_directives().items()}
        metadata, options = doc["metadata"], doc["options"]

        field_falues = ((f, metadata.get(f)) for f in potential)
        fields = [f for f, v in field_falues if isinstance(v, Directive)]

        dynamic = {f: metadata.pop(f, None) for f in fields}
        if "version" not in metadata and "version" not in dynamic:
            msg = (
                "No `version` was found in `[metadata]`, `ini2toml` will assume it is "
                "defined by tools like `setuptools-scm` or in `setup.py`. "
                "Automatically adding it to `dynamic` (in accordance with PEP 621)"
            )
            _logger.debug(msg)
            fields.insert(0, "version")

        extras: List[str] = []
        ep = metadata.pop("entry-points", options.pop("entry-points", None))
        if isinstance(ep, Directive):
            fields.append("entry-points")
            dynamic["entry-points"] = ep
            extras = ["scripts", "gui-scripts"]
        if not fields:
            return doc
        metadata.setdefault("dynamic", []).extend(fields + extras)

        if dynamic:
            doc.setdefault("options.dynamic", IR()).update(dynamic)
            # ^ later `options.dynamic` is converted to `tool.setuptools.dynamic`
        return doc

    def fix_extras_require(self, doc: R) -> R:
        """`extras-require` can have markers embeded in the extra group
        they need to be removed and added to the dependencies themselves
        """
        if "project:optional-dependencies" not in doc:
            return doc

        extras = doc["project:optional-dependencies"]
        keys = list(extras.keys())  # Eager, so we can modify extras
        for key in keys:
            if not isinstance(key, str):
                continue
            extra_name, _, marker = key.partition(":")
            extra_name, marker = extra_name.strip(), marker.strip()
            if not marker:
                continue
            values = extras[key]
            extras.rename(key, extra_name)
            extras[extra_name] = [_add_marker(r, marker) for r in values.as_list()]

        return doc

    def move_setup_requires(self, doc: R) -> R:
        """Move ``setup_requires`` to the equivalent field in :pep:`518`, and add
        mandatory build dependencies if they are missing and
        """
        options = doc["options"]
        build_system = doc["build-system"]
        if "setup-requires" in options:
            msg = "The field 'setup_requires' is deprecated. "
            msg += "Converting to `build-system.requires` as specified by PEP 518."
            warnings.warn(msg, DeprecationWarning)
            requirements: CommentedList[str] = options.pop("setup-requires")
            # Deduplicate
            existing = {Requirement(r).name: r for r in requirements.as_list()}
            mandatory = {
                Requirement(r).name: r
                for r in chain(build_system.get("requires", []), self.BUILD_REQUIRES)
            }
            new = [r for name, r in mandatory.items() if name not in existing]
            for req in reversed(new):
                requirements.insert_line(0, (req,))
            build_system["requires"] = requirements

        return doc

    def move_tests_require(self, doc: R) -> R:
        """Move ``tests_require`` to a ``testing`` extra as optional dependency
        (this option is deprecated in setuptools (the test command is deprecated).

        It assumes ``move_options_missing_in_pep621`` already run (to populate
        ``project:optional-dependencies``.
        """
        if "tests-require" in doc["options"]:
            msg = "The field 'tests_require' is deprecated and no longer supported. "
            msg += "Dependencies will be converted to optional (`testing` extra). "
            msg += "You can use a tool like `tox` or `nox` to replace this workflow."
            warnings.warn(msg, DeprecationWarning)
            reqs: CommentedList[str] = doc["options"].pop("tests-require")
            if "project:optional-dependencies" not in doc:
                doc["project:optional-dependencies"] = IR(testing=reqs)
                return doc

            opt_deps = doc["project:optional-dependencies"]
            if "testing" not in opt_deps:
                opt_deps["testing"] = reqs

            testing: CommentedList[str] = opt_deps["testing"]
            test_deps = {Requirement(r).name: r for r in reqs.as_list()}
            existing_deps = {Requirement(r).name: r for r in testing.as_list()}
            new = [r for name, r in test_deps.items() if name not in existing_deps]
            for req in new:
                testing.insert_line(len(testing), (req,))

        return doc

    def make_include_package_data_explicit(self, doc: R) -> R:
        options = doc["options"]
        if "include-package-data" not in options:
            # This allows setuptools to decide to change the default from False to True,
            # when adopting PEP 621
            options["include-package-data"] = False

        return doc

    def parse_setup_py_command_options(self, doc: R) -> R:
        """``distutils`` commands can accept arguments from ``setup.cfg`` files.
        This function moves these arguments to their own ``distutils``
        tool-specific sub-table
        """
        sections = list(doc.keys())
        commands = _distutils_commands()
        for k in sections:
            if isinstance(k, str) and k in commands:
                section = self._be.apply_best_effort_to_section(doc[k])
                for option in section:
                    if isinstance(option, str):
                        section.rename(option, self.normalise_key(option))
                doc[k] = section
                doc.rename(k, ("distutils", k))
        return doc

    def split_subtables(self, out: R) -> R:
        """``setuptools`` emulate nested sections (e.g.: ``options.extras_require``)
        which can be directly expressed in TOML via sub-tables.
        """
        sections = [
            k
            for k in out.keys()
            if isinstance(k, str) and (k.startswith("options.") or ":" in k)
        ]
        for section in sections:
            new_key = SECTION_SPLITTER.split(section)
            if section.startswith("options."):
                new_key = ["tool", "setuptools", *new_key[1:]]
            out.rename(section, tuple(new_key))
        return out

    def ensure_pep518(self, doc: R) -> R:
        """:pep:`518` specifies that any other tool adding configuration under
        ``pyproject.toml`` should use the ``tool`` table. This means that the only
        top-level keys are ``build-system``, ``project`` and ``tool``.
        """
        allowed = ("build-system", "project", "tool", "metadata", "options")
        allowed_prefixes = ("options.", "project:")
        for k in list(doc.keys()):
            key = k
            rest: Sequence = ()
            if isinstance(k, tuple) and not isinstance(key, HiddenKey):
                key, *rest = k
            if isinstance(key, HiddenKey):
                continue
            if not (key in allowed or any(key.startswith(p) for p in allowed_prefixes)):
                doc.rename(k, ("tool", key, *rest))
        return doc

    def pep621_transform(self, doc: R) -> R:
        """Rules are applied sequentially and therefore can interfere with the following
        ones. Please notice that renaming is applied after value processing.
        """
        transformations = [
            # --- value processing and type changes ---
            self.apply_value_processing,
            # --- transformations mainly focusing on PEP 621 ---
            self.merge_and_rename_urls,
            self.merge_authors_maintainers_and_emails,
            self.merge_and_rename_long_description_and_content_type,
            self.handle_license_and_files,
            self.move_and_split_entrypoints,
            self.move_options_missing_in_pep621,
            self.remove_metadata_not_in_pep621,
            # --- General fixes
            self.fix_extras_require,
            self.rename_script_files,
            self.handle_packages_find,
            self.handle_dynamic,
            self.move_setup_requires,
            self.move_tests_require,
            self.make_include_package_data_explicit,
            # --- distutils ---
            self.parse_setup_py_command_options,
            # --- final steps ---
            self.split_subtables,
            self.ensure_pep518,
        ]
        out = self.template(doc.__class__)
        out.update(doc)
        out.setdefault("metadata", IR())
        out.setdefault("options", IR())
        out = reduce(apply, transformations, out)
        out.rename("metadata", "project", ignore_missing=True)
        out.rename("options", ("tool", "setuptools"), ignore_missing=True)
        return out

    def normalise_keys(self, cfg: R) -> R:
        """Normalise keys in ``setup.cfg``, by replacing aliases with cannonic names
        and replacing the snake case with kebab case.

        .. note:: Although setuptools recently deprecated kebab case in ``setup.cfg``
           ``pyproject.toml`` use it as a convention (as established in :pep:`517`,
           :pep:`518` and :pep:`621`) so this normalisation makes more sense for the
           translation.
        """
        # Normalise for the same convention as pyproject
        for i in range(len(cfg.order)):
            section_name = cfg.order[i]
            if not isinstance(section_name, str):
                continue
            if not any(section_name.startswith(s) for s in SETUPTOOLS_SECTIONS):
                continue
            section = cfg[section_name]
            cfg.rename(section_name, kebab_case(section_name))
            if any(section_name.startswith(s) for s in SKIP_CHILD_NORMALISATION):
                continue
            for j in range(len(section.order)):
                option_name = section.order[j]
                if not isinstance(option_name, str):
                    continue
                section.rename(option_name, self.normalise_key(option_name))
        # Normalise aliases
        metadata = cfg.get("metadata")
        if not metadata:
            return cfg
        for alias, cannonic in self.setupcfg_aliases().items():
            if alias in metadata:
                msg = f"{alias!r} is deprecated. Translating to {cannonic!r} instead."
                warnings.warn(msg, DeprecationWarning)
                metadata.rename(alias, cannonic)
        return cfg

    def normalise_key(self, key: str) -> str:
        """Normalise a single key for option"""
        return kebab_case(key)


# ---- Helpers ----


class Directive(dict):
    """Represent a setuptools' setup.cfg directive (e.g 'file:', 'attr:')

    In TOML these directives can be represented as dict-like objects, however in the
    conversion algorithm we need to be able to differentiate between them.
    By inheriting from dict, we can use directive classes interchangeably but also check
    using `isinstance(obj, Directive)`.
    """

    def __init__(self, kind: str, args: Any):
        self.kind = kind
        self.args = Any
        super().__init__(((kind, args),))


def directive(*directives: str, orelse=split_comment):
    """:obj:`~functools.partial` form of :func:`split_directive`"""
    directives = directives or ("file", "attr")
    return partial(split_directive, directives=directives, orelse=orelse)


def split_directive(
    value: str, directives: Sequence[str] = ("file", "attr"), orelse=split_comment
):
    candidates = (d for d in directives if value.strip().startswith(f"{d}:"))
    directive = next(candidates, None)
    if directive is None:
        return orelse(value)

    raw_value = value.lstrip()[len(directive) + 1 :].strip()
    if directive == "file":
        return Directive(directive, split_list_comma(raw_value))
    return Directive(directive, split_comment(raw_value))


def value_error(field: str):
    """Simply raise a :exc:`ValueError` when used as a transformation function"""

    def _fn(value):
        raise ValueError(f"Invalid value for {field!r}: {value!r}")

    return _fn


def _distutils_commands() -> Set[str]:
    try:
        from . import iterate_entry_points

        commands = [ep.name for ep in iterate_entry_points("distutils.commands")]
    except Exception:
        commands = []
    return {*commands, *COMMAND_SECTIONS}


def _ensure_where_list(where):
    if isinstance(where, Commented):
        return where.as_commented_list()

    return [where]


def _add_marker(dep: str, marker: str) -> str:
    joiner = " and " if ";" in dep else "; "
    return joiner.join((dep, marker))


def split_deps(value):
    """Setuptools seem to accept line continuations for markers
    (with comments in the middle), and that is more difficult to process.
    e.g.: https://github.com/jaraco/zipp
    """
    internal: CommentedList[str] = split_list_semi(value)
    lines = list(internal)
    L = len(lines)
    i = j = 0
    remove = []
    while i < L:
        line = lines[i]
        if line.comment_only() or not line.value:
            i += 1
            continue
        while line.value and line.value[-1].strip()[-1] == "\\":
            comments: List[Tuple(int, str)] = []
            for j in range(i + 1, L):
                # Find the non commented / non empty line
                following = lines[j]
                if following.value_or(None):
                    line = _fuse_lines(line, following)
                    lines[i] = line
                    if len(comments) == 1 and not line.has_comment():
                        # If just one comment was found in between,
                        # use it as a inline comment
                        remove.append(comments[0][0])
                        line.comment = comments[0][1]
                    remove.append(j)
                    i = j
                    break
                if following.comment:
                    # Store the comments, they might be used as inline
                    comments.append((j, following.comment))
        i += 1

    for i in reversed(remove):  # backwards otherwise we lose track of the indexes
        lines.pop(i)

    return CommentedList(lines)


def _fuse_lines(line1: Commented[List[str]], line2: Commented[List[str]]):
    """Fuse 2 lines in a CommentedList that accidentally split a single
    value between them
    """
    values1 = line1.value
    values2 = line2.value
    # Requires line1 and line2 to not be empty
    assert isinstance(values1, list) and isinstance(values2, list)
    keep1, keep2 = values1[:-1], values2[1:]
    shared = values1[-1].strip().strip("\\").strip() + " " + values2[0].strip()
    return Commented(keep1 + [shared] + keep2, line2.comment)
