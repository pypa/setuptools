"""Extensions to the 'distutils' for large or complex distributions"""

import distutils.core, setuptools.command
from setuptools.dist import Distribution, Feature
from setuptools.extension import Extension
from setuptools.depends import Require
from distutils.core import Command as _Command
from distutils.util import convert_path
import os.path

__version__ = '0.0.1'

__all__ = [
    'setup', 'Distribution', 'Feature', 'Command', 'Extension', 'Require',
    'find_packages'
]


def find_packages(where='.'):
    """Return a list all Python packages found within directory 'where'

    'where' should be supplied as a "cross-platform" (i.e. URL-style) path; it
    will be converted to the appropriate local path syntax.
    """

    out = []
    stack=[(convert_path(where), '')]

    while stack:
        where,prefix = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where,name)
            if (os.path.isdir(fn) and
                os.path.isfile(os.path.join(fn,'__init__.py'))
            ):
                out.append(prefix+name); stack.append((fn,prefix+name+'.'))
    return out




def setup(**attrs):
    """Do package setup

    This function takes the same arguments as 'distutils.core.setup()', except
    that the default distribution class is 'setuptools.dist.Distribution'.  See
    that class' documentation for details on the new keyword arguments that it
    makes available via this function.
    """
    attrs.setdefault("distclass",Distribution)
    return distutils.core.setup(**attrs)
    

class Command(_Command):
    __doc__ = _Command.__doc__

    command_consumes_arguments = False

    def reinitialize_command(self, command, reinit_subcommands=0, **kw):
        cmd = _Command.reinitialize_command(self, command, reinit_subcommands)
        for k,v in kw.items():
            setattr(cmd,k,v)    # update command with keywords
        return cmd



















