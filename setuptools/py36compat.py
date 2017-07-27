import sys
from distutils.errors import DistutilsOptionError
from distutils.util import strtobool
from distutils.debug import DEBUG

from setuptools.extern import six


class Distribution_parse_config_files:
    """
    Mix-in providing forward-compatibility for functionality
    presumed to be included by default on Python 3.7. See
    http://bugs.python.org/issue20754 and #889 for details.

    Do not edit the code in this class except to update functionality
    as implemented in distutils.
    """
    def parse_config_files(self, filenames=None):
        from configparser import ConfigParser

        # Ignore install directory options if we have a venv
        if sys.prefix != sys.base_prefix:
            ignore_options = [
                'install-base', 'install-platbase', 'install-lib',
                'install-platlib', 'install-purelib', 'install-headers',
                'install-scripts', 'install-data', 'prefix', 'exec-prefix',
                'home', 'user', 'root']
        else:
            ignore_options = []

        ignore_options = frozenset(ignore_options)

        if filenames is None:
            filenames = self.find_config_files()

        if DEBUG:
            self.announce("Distribution.parse_config_files():")

        parser = ConfigParser(interpolation=None)
        for filename in filenames:
            if DEBUG:
                self.announce("  reading %s" % filename)
            parser.read(filename)
            for section in parser.sections():
                options = parser.options(section)
                opt_dict = self.get_option_dict(section)

                for opt in options:
                    if opt != '__name__' and opt not in ignore_options:
                        val = parser.get(section,opt)
                        opt = opt.replace('-', '_')
                        opt_dict[opt] = (filename, val)

            # Make the ConfigParser forget everything (so we retain
            # the original filenames that options come from)
            parser.__init__(interpolation=None)

        # If there was a "global" section in the config file, use it
        # to set Distribution options.

        if 'global' in self.command_options:
            for (opt, (src, val)) in self.command_options['global'].items():
                alias = self.negative_opt.get(opt)
                try:
                    if alias:
                        setattr(self, alias, not strtobool(val))
                    elif opt in ('verbose', 'dry_run'): # ugh!
                        setattr(self, opt, strtobool(val))
                    else:
                        setattr(self, opt, val)
                except ValueError as msg:
                    raise DistutilsOptionError(msg)

    def parse_config_files_py2(self, filenames=None):
        """
        Backport of the Python 3 implementation. Since `interpolation`
        isn't available as a parameter, use the RawConfigParser instead.
        """
        from ConfigParser import RawConfigParser

        # no venv on Python 2
        ignore_options = frozenset([])

        if filenames is None:
            filenames = self.find_config_files()

        if DEBUG:
            self.announce("Distribution.parse_config_files():")

        parser = RawConfigParser()
        for filename in filenames:
            if DEBUG:
                self.announce("  reading %s" % filename)
            parser.read(filename)
            for section in parser.sections():
                options = parser.options(section)
                opt_dict = self.get_option_dict(section)

                for opt in options:
                    if opt != '__name__' and opt not in ignore_options:
                        val = parser.get(section,opt)
                        opt = opt.replace('-', '_')
                        opt_dict[opt] = (filename, val)

            # Make the ConfigParser forget everything (so we retain
            # the original filenames that options come from)
            parser.__init__()

        # If there was a "global" section in the config file, use it
        # to set Distribution options.

        if 'global' in self.command_options:
            for (opt, (src, val)) in self.command_options['global'].items():
                alias = self.negative_opt.get(opt)
                try:
                    if alias:
                        setattr(self, alias, not strtobool(val))
                    elif opt in ('verbose', 'dry_run'): # ugh!
                        setattr(self, opt, strtobool(val))
                    else:
                        setattr(self, opt, val)
                except ValueError as msg:
                    raise DistutilsOptionError(msg)

    if six.PY2:
        parse_config_files = parse_config_files_py2


if False:
    # When updated behavior is available upstream,
    # disable override here.
    del Distribution_parse_config_files.parse_config_files
