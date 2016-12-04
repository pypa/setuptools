import io
import os
import sys
from functools import partial

from distutils.errors import DistutilsOptionError
from setuptools.py26compat import import_module
from setuptools.extern.six import string_types


class ConfigHandler(object):
    """Handles metadata supplied in configuration files."""

    section_prefix = None
    """Prefix for config sections handled by this handler.
    Must be provided by class heirs.

    """

    strict_mode = True
    """Flag. Whether unknown options in config should
    raise DistutilsOptionError exception, or pass silently.

    """

    def __init__(self, target_obj, options):
        sections = {}

        section_prefix = self.section_prefix
        for section_name, section_options in options.items():
            if not section_name.startswith(section_prefix):
                continue

            section_name = section_name.replace(section_prefix, '').strip(':')
            sections[section_name] = section_options

        self.target_obj = target_obj
        self.sections = sections

    @property
    def parsers(self):
        """Metadata item name to parser function mapping."""
        raise NotImplementedError(
            '%s must provide .parsers property' % self.__class__.__name__)

    def __setitem__(self, option_name, value):
        unknown = tuple()
        target_obj = self.target_obj

        current_value = getattr(target_obj, option_name, unknown)

        if current_value is unknown:
            raise KeyError(option_name)

        if current_value:
            # Already inhabited. Skipping.
            return

        parser = self.parsers.get(option_name)
        if parser:
            value = parser(value)

        setter = getattr(target_obj, 'set_%s' % option_name, None)
        if setter is None:
            setattr(target_obj, option_name, value)
        else:
            setter(value)

    @classmethod
    def _parse_list(cls, value, separator=','):
        """Represents value as a list.

        Value is split either by comma or by lines.

        :param value:
        :param separator: List items separator character.
        :rtype: list
        """
        if isinstance(value, list):  # _parse_complex case
            return value

        if '\n' in value:
            value = value.splitlines()
        else:
            value = value.split(separator)

        return [chunk.strip() for chunk in value]

    @classmethod
    def _parse_dict(cls, value):
        """Represents value as a dict.

        :param value:
        :rtype: dict
        """
        separator = '='
        result = {}
        for line in cls._parse_list(value):
            key, sep, val = line.partition(separator)
            if sep != separator:
                raise DistutilsOptionError(
                    'Unable to parse option value to dict: %s' % value)
            result[key.strip()] = val.strip()

        return result

    @classmethod
    def _parse_bool(cls, value):
        """Represents value as boolean.

        :param value:
        :rtype: bool
        """
        value = value.lower()
        return value in ('1', 'true', 'yes')

    @classmethod
    def _parse_file(cls, value):
        """Represents value as a string, allowing including text
        from nearest files using include().

        Examples:
            include: LICENSE
            include: src/file.txt

        :param str value:
        :rtype: str
        """
        if not isinstance(value, string_types):
            return value

        include_directive = 'file:'
        if not value.startswith(include_directive):
            return value

        filepath = value.replace(include_directive, '').strip()

        if os.path.isfile(filepath):
            with io.open(filepath, encoding='utf-8') as f:
                value = f.read()

        return value

    @classmethod
    def _get_parser_compound(cls, *parse_methods):
        """Returns parser function to represents value as a list.

        Parses a value applying given methods one after another.

        :param parse_methods:
        :rtype: callable
        """
        def parse(value):
            parsed = value

            for method in parse_methods:
                parsed = method(parsed)

            return parsed

        return parse

    @classmethod
    def _parse_section_to_dict(cls, section_options, values_parser=None):
        """Parses section options into a dictionary.

        Optionally applies a given parser to values.

        :param dict section_options:
        :param callable values_parser:
        :rtype: dict
        """
        value = {}
        values_parser = values_parser or (lambda val: val)
        for key, (_, val) in section_options.items():
            value[key] = values_parser(val)
        return value

    def parse_section(self, section_options):
        """Parses configuration file section.

        :param dict section_options:
        """
        for (name, (_, value)) in section_options.items():
            try:
                self[name] = value

            except KeyError:
                if self.strict_mode:
                    raise DistutilsOptionError(
                        'Unknown distribution option: %s' % name)

    def parse(self):
        """Parses configuration file items from one
        or more related sections.

        """
        for section_name, section_options in self.sections.items():

            method_postfix = ''
            if section_name:  # [section:option] variant
                method_postfix = '_%s' % section_name

            section_parser_method = getattr(
                self, 'parse_section%s' % method_postfix, None)

            if section_parser_method is None:
                raise DistutilsOptionError(
                    'Unsupported distribution option section: [%s:%s]' % (
                        self.section_prefix, section_name))

            section_parser_method(section_options)


class ConfigMetadataHandler(ConfigHandler):

    section_prefix = 'metadata'
    strict_mode = False
    """We need to keep it loose, to be compatible with `pbr` package
    which also uses `metadata` section.

    """

    @property
    def parsers(self):
        """Metadata item name to parser function mapping."""
        parse_list = self._parse_list
        parse_file = self._parse_file

        return {
            'platforms': parse_list,
            'keywords': parse_list,
            'provides': parse_list,
            'requires': parse_list,
            'obsoletes': parse_list,
            'classifiers': self._get_parser_compound(parse_file, parse_list),
            'license': parse_file,
            'description': parse_file,
            'long_description': parse_file,
            'version': self._parse_version,
        }

    def parse_section_classifiers(self, section_options):
        """Parses configuration file section.

        :param dict section_options:
        """
        classifiers = []
        for begin, (_, rest) in section_options.items():
            classifiers.append('%s :%s' % (begin.title(), rest))

        self['classifiers'] = classifiers

    def _parse_version(self, value):
        """Parses `version` option value.

        :param value:
        :rtype: str

        """
        attr_directive = 'attr:'
        if not value.startswith(attr_directive):
            return value

        attrs_path = value.replace(attr_directive, '').strip().split('.')
        attr_name = attrs_path.pop()

        module_name = '.'.join(attrs_path)
        module_name = module_name or '__init__'

        sys.path.insert(0, os.getcwd())
        try:
            module = import_module(module_name)
            version = getattr(module, attr_name)

            if callable(version):
                version = version()

            if not isinstance(version, string_types):
                if hasattr(version, '__iter__'):
                    version = '.'.join(map(str, version))
                else:
                    version = '%s' % version

        finally:
            sys.path = sys.path[1:]

        return version


class ConfigOptionsHandler(ConfigHandler):

    section_prefix = 'options'

    @property
    def parsers(self):
        """Metadata item name to parser function mapping."""
        parse_list = self._parse_list
        parse_list_semicolon = partial(self._parse_list, separator=';')
        parse_bool = self._parse_bool
        parse_dict = self._parse_dict

        return {
            'zip_safe': parse_bool,
            'use_2to3': parse_bool,
            'include_package_data': parse_bool,
            'package_dir': parse_dict,
            'use_2to3_fixers': parse_list,
            'use_2to3_exclude_fixers': parse_list,
            'convert_2to3_doctests': parse_list,
            'scripts': parse_list,
            'eager_resources': parse_list,
            'dependency_links': parse_list,
            'namespace_packages': parse_list,
            'install_requires': parse_list_semicolon,
            'setup_requires': parse_list_semicolon,
            'tests_require': parse_list_semicolon,
            'packages': self._parse_packages,
            'entry_points': self._parse_file,
        }

    def _parse_packages(self, value):
        """Parses `packages` option value.

        :param value:
        :rtype: list
        """
        find_directive = 'find:'

        if not value.startswith(find_directive):
            return self._parse_list(value)

        from setuptools import find_packages
        return find_packages()

    def parse_section_dependency_links(self, section_options):
        """Parses `dependency_links` configuration file section.

        :param dict section_options:
        """
        parsed = self._parse_section_to_dict(section_options)
        self['dependency_links'] = list(parsed.values())

    def parse_section_entry_points(self, section_options):
        """Parses `entry_points` configuration file section.

        :param dict section_options:
        """
        parsed = self._parse_section_to_dict(section_options, self._parse_list)
        self['entry_points'] = parsed

    def _parse_package_data(self, section_options):
        parsed = self._parse_section_to_dict(section_options, self._parse_list)

        root = parsed.get('*')
        if root:
            parsed[''] = root
            del parsed['*']

        return parsed

    def parse_section_package_data(self, section_options):
        """Parses `package_data` configuration file section.

        :param dict section_options:
        """
        self['package_data'] = self._parse_package_data(section_options)

    def parse_section_exclude_package_data(self, section_options):
        """Parses `exclude_package_data` configuration file section.

        :param dict section_options:
        """
        self['exclude_package_data'] = self._parse_package_data(
            section_options)

    def parse_section_extras_require(self, section_options):
        """Parses `extras_require` configuration file section.

        :param dict section_options:
        """
        parse_list = partial(self._parse_list, separator=';')
        self['extras_require'] = self._parse_section_to_dict(
            section_options, parse_list)
