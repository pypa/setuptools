"""Bootstrap module to download/quasi-install 'setuptools' package

Usage::

   from setuptools_boot import require_version
   require_version('0.0.1')

   from setuptools import setup, Extension, ...

Note that if a suitable version of 'setuptools' is not found on 'sys.path',
it will be downloaded and installed to the current directory.  This means
that if you are using 'setuptools.find_packages()' in the same directory, you
will need to exclude the setuptools package from the distribution (unless you
want setuptools to be installed as part of your distribution).  To do this,
you can simply use:

    setup(
        # ...
        packages = [pkg for pkg in find_packages()
                        if not pkg.startswith('setuptools')
        ],
        # ...
    )

to eliminate the setuptools packages from consideration.  However, if you are
using a 'lib' or 'src' directory to contain your distribution's packages, this
will not be an issue.
"""

from distutils.version import StrictVersion
from distutils.util import convert_path
import os.path

__all__ = ['require_version']







def require_version(version='0.0.1', dlbase='file:../../setuptools/dist'):
    """Request to use setuptools of specified version

    'dlbase', if provided, is the base URL that should be used to download
    a particular version of setuptools.  '/setuptools-VERSION.zip' will be
    added to 'dlbase' to construct the download URL, if a download is needed.

    XXX current dlbase works for local testing only
    """

    if StrictVersion(version) > get_installed_version():
        unload_setuptools()
        download_setuptools(version,dlbase)

    if StrictVersion(version) > get_installed_version():
        # Should never get here
        raise SystemExit(
            "Downloaded new version of setuptools, but it's not on sys.path"
        )


def get_installed_version():
    """Return version of currently-installed setuptools, or '"0.0.0"'"""
    try:
        from setuptools import __version__
        return __version__
    except ImportError:
        return '0.0.0'


def download_setuptools(version,dlbase):
    """Download setuptools-VERSION.zip from dlbase and extract in local dir"""
    basename = 'setuptools-%s' % version
    filename = basename+'.zip'
    url = '%s/%s' % (dlbase,filename)
    download_file(url,filename)
    extract_zipdir(filename,basename+'/setuptools','setuptools')




def unload_setuptools():
    """Unload the current (outdated) 'setuptools' version from memory"""
    import sys
    for k in sys.modules.keys():
        if k.startswith('setuptools.') or k=='setuptools':
            del sys.modules[k]


def download_file(url,filename):
    """Download 'url', saving to 'filename'"""
    from urllib2 import urlopen
    f = urlopen(url); bytes = f.read(); f.close()
    f = open(filename,'wb'); f.write(bytes); f.close()


def extract_zipdir(filename,zipdir,targetdir):
    """Unpack zipfile 'filename', extracting 'zipdir' to 'targetdir'"""

    from zipfile import ZipFile

    f = ZipFile(filename)
    if zipdir and not zipdir.endswith('/'):
        zipdir+='/'
    plen = len(zipdir)
    paths = [
        path for path in f.namelist()
             if path.startswith(zipdir) and not path.endswith('/')
    ]
    paths.sort()
    paths.reverse() # unpack in reverse order so __init__ goes last!

    for path in paths:
        out = os.path.join(targetdir,convert_path(path[plen:]))
        dir = os.path.dirname(out)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        out=open(out,'wb'); out.write(f.read(path)); out.close()

    f.close()


