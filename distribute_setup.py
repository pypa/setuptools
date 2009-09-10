#!python
"""Bootstrap distribute installation

If you want to use setuptools in your package's setup.py, just include this
file in the same directory with it, and add this to the top of your setup.py::

    from distribute_setup import use_setuptools
    use_setuptools()

If you want to require a specific version of setuptools, set a download
mirror, or use an alternate download directory, you can do so by supplying
the appropriate options to ``use_setuptools()``.

This file can also be run as a script to install or upgrade setuptools.
"""
try:
    from site import USER_SITE
except ImportError:
    USER_SITE = None

import sys
import os
import time
import fnmatch
from distutils import log
import subprocess

IS_JYTHON = sys.platform.startswith('java')
DEFAULT_VERSION = "0.6.2"
DEFAULT_URL     = "http://pypi.python.org/packages/source/d/distribute/"

def quote(c):
    if sys.platform == 'win32':
        if ' ' in c:
            return '"%s"' % c
    return c

def python_cmd(cmd):
    python = quote(sys.executable)
    cmd = quote(cmd)
    if IS_JYTHON:
        return subprocess.Popen([python, cmd]).wait() == 0
    args = [os.P_WAIT, python, python] + cmd.split() + [os.environ]
    return os.spawnle(*args) == 0

def _install(tarball):
    # extracting the tarball
    tmpdir = tempfile.mkdtemp()
    log.warn('Extracting in %s' % tmpdir)
    old_wd = os.getcwd()
    try:
        os.chdir(tmpdir)
        tar = tarfile.open(tarball)
        extractall(tar)
        tar.close()

        # going in the directory
        subdir = os.path.join(tmpdir, os.listdir(tmpdir)[0])
        os.chdir(subdir)
        log.warn('Now working in %s' % subdir)

        # installing
        assert python_cmd('setup.py -q install')
    finally:
        os.chdir(old_wd)

def _build_egg(tarball, to_dir=os.curdir):
    # extracting the tarball
    tmpdir = tempfile.mkdtemp()
    log.warn('Extracting in %s' % tmpdir)
    old_wd = os.getcwd()
    try:
        os.chdir(tmpdir)
        tar = tarfile.open(tarball)
        extractall(tar)
        tar.close()

        # going in the directory
        subdir = os.path.join(tmpdir, os.listdir(tmpdir)[0])
        os.chdir(subdir)
        log.warn('Now working in %s' % subdir)

        # building an egg
        python_cmd('setup.py -v -q bdist_egg --dist-dir %s' % to_dir)

        # returning the result
        for file in os.listdir(to_dir):
            if fnmatch.fnmatch(file, 'distribute-%s*.egg' % DEFAULT_VERSION):
                return os.path.join(to_dir, file)

        raise IOError('Could not build the egg.')
    finally:
        os.chdir(old_wd)

def _do_download(version=DEFAULT_VERSION, download_base=DEFAULT_URL,
                 to_dir=os.curdir, download_delay=15):
    tarball = download_setuptools(version, download_base,
                                  to_dir, download_delay)
    egg = _build_egg(tarball, to_dir)
    sys.path.insert(0, egg)
    import setuptools
    setuptools.bootstrap_install_from = egg

def use_setuptools(
    version=DEFAULT_VERSION, download_base=DEFAULT_URL, to_dir=os.curdir,
    download_delay=15
):
    was_imported = 'pkg_resources' in sys.modules or 'setuptools' in sys.modules
    try:
        import pkg_resources
        if not hasattr(pkg_resources, '_distribute'):
            raise ImportError
    except ImportError:
        return _do_download(version, download_base, to_dir, download_delay)
    try:
        pkg_resources.require("distribute>="+version); return
    except pkg_resources.VersionConflict, e:
        if was_imported:
            print >>sys.stderr, (
            "The required version of distribute (>=%s) is not available, and\n"
            "can't be installed while this script is running. Please install\n"
            " a more recent version first, using 'easy_install -U distribute'."
            "\n\n(Currently using %r)"
            ) % (version, e.args[0])
            sys.exit(2)
        else:
            del pkg_resources, sys.modules['pkg_resources']    # reload ok
            return _do_download(version, download_base, to_dir, download_delay)
    except pkg_resources.DistributionNotFound:
        return _do_download(version, download_base, to_dir, download_delay)

def download_setuptools(
    version=DEFAULT_VERSION, download_base=DEFAULT_URL, to_dir=os.curdir,
    delay=15,
):
    """Download distribute from a specified location and return its filename

    `version` should be a valid distribute version number that is available
    as an egg for download under the `download_base` URL (which should end
    with a '/'). `to_dir` is the directory where the egg will be downloaded.
    `delay` is the number of seconds to pause before an actual download attempt.
    """
    import urllib2
    tgz_name = "distribute-%s.tar.gz" % version
    url = download_base + tgz_name
    saveto = os.path.join(to_dir, tgz_name)
    src = dst = None
    if not os.path.exists(saveto):  # Avoid repeated downloads
        try:
            from distutils import log
            log.warn("Downloading %s", url)
            src = urllib2.urlopen(url)
            # Read/write all in one block, so we don't create a corrupt file
            # if the download is interrupted.
            data = src.read()
            dst = open(saveto, "wb")
            dst.write(data)
        finally:
            if src:
                src.close()
            if dst:
                dst.close()
    return os.path.realpath(saveto)


SETUPTOOLS_PKG_INFO  = """\
Metadata-Version: 1.0
Name: setuptools
Version: 0.6c9
Summary: xxxx
Home-page: xxx
Author: xxx
Author-email: xxx
License: xxx
Description: xxx
"""

def _patch_file(path, content):
    """Will backup the file then patch it"""
    existing_content = open(path).read()
    if existing_content == content:
        # already patched
        log.warn('Already patched.')
        return False
    log.warn('Patching...')
    _rename_path(path)
    f = open(path, 'w')
    try:
        f.write(content)
    finally:
        f.close()
    return True

def _same_content(path, content):
    return open(path).read() == content

def _rename_path(path):
    new_name = path + '.OLD.%s' % time.time()
    log.warn('Renaming %s into %s' % (path, new_name))
    try:
        from setuptools.sandbox import DirectorySandbox
        def _violation(*args):
            pass
        DirectorySandbox._violation = _violation
    except ImportError:
        pass

    os.rename(path, new_name)
    return new_name

def _remove_flat_installation(placeholder):
    if not os.path.isdir(placeholder):
        log.warn('Unkown installation at %s' % placeholder)
        return False
    found = False
    for file in os.listdir(placeholder):
        if fnmatch.fnmatch(file, 'setuptools*.egg-info'):
            found = True
            break
    if not found:
        log.warn('Could not locate setuptools*.egg-info')
    else:
        log.warn('Removing elements out of the way...')
        pkg_info = os.path.join(placeholder, file)
        if os.path.isdir(pkg_info):
            patched = _patch_egg_dir(pkg_info)
        else:
            patched = _patch_file(pkg_info, SETUPTOOLS_PKG_INFO)

    if not patched:
        log.warn('%s already patched.' % pkg_info)
        return False
    # now let's move the files out of the way
    for element in ('setuptools', 'pkg_resources.py', 'site.py'):
        element = os.path.join(placeholder, element)
        if os.path.exists(element):
            _rename_path(element)
        else:
            log.warn('Could not find the %s element of the '
                     'Setuptools distribution' % element)
    return True

def after_install(dist):
    log.warn('After install bootstrap.')
    placeholder = dist.get_command_obj('install').install_purelib
    if not os.path.exists(placeholder):
        log.warn('Could not find the install location')
        return
    pyver = '%s.%s' % (sys.version_info[0], sys.version_info[1])
    setuptools_file = 'setuptools-0.6c9-py%s.egg-info' % pyver
    pkg_info = os.path.join(placeholder, setuptools_file)
    if os.path.exists(pkg_info):
        log.warn('%s already exists' % pkg_info)
        return
    log.warn('Creating %s' % pkg_info)
    f = open(pkg_info, 'w')
    try:
        f.write(SETUPTOOLS_PKG_INFO)
    finally:
        f.close()
    pth_file = os.path.join(placeholder, 'setuptools.pth')
    log.warn('Creating %s' % pth_file)
    f = open(pth_file, 'w')
    try:
        f.write(os.path.join(os.curdir, setuptools_file))
    finally:
        f.close()

def _patch_egg_dir(path):
    # let's check if it's already patched
    pkg_info = os.path.join(path, 'EGG-INFO', 'PKG-INFO')
    if os.path.exists(pkg_info):
        if _same_content(pkg_info, SETUPTOOLS_PKG_INFO):
            log.warn('%s already patched.' % pkg_info)
            return False
    _rename_path(path)
    os.mkdir(path)
    os.mkdir(os.path.join(path, 'EGG-INFO'))
    pkg_info = os.path.join(path, 'EGG-INFO', 'PKG-INFO')
    f = open(pkg_info, 'w')
    try:
        f.write(SETUPTOOLS_PKG_INFO)
    finally:
        f.close()
    return True

def before_install():
    log.warn('Before install bootstrap.')
    fake_setuptools()

def _under_prefix(location):
    if 'install' not in sys.argv:
        return True
    args = sys.argv[sys.argv.index('install')+1:]
    for index, arg in enumerate(args):
        for option in ('--root', '--prefix'):
            if arg.startswith('%s=' % option):
                top_dir = arg.split('root=')[-1]
                return location.startswith(top_dir)
            elif arg == option:
                if len(args) > index:
                    top_dir = args[index+1]
                    return location.startswith(top_dir)
            elif option == '--user' and USER_SITE is not None:
                return location.startswith(USER_SITE)
    return True

def fake_setuptools():
    log.warn('Scanning installed packages')
    try:
        import pkg_resources
    except ImportError:
        # we're cool
        log.warn('Setuptools or Distribute does not seem to be installed.')
        return
    ws = pkg_resources.working_set
    setuptools_dist = ws.find(pkg_resources.Requirement.parse('setuptools'))
    if setuptools_dist is None:
        log.warn('No setuptools distribution found')
        return
    # detecting if it was already faked
    setuptools_location = setuptools_dist.location
    log.warn('Setuptools installation detected at %s' % setuptools_location)

    # if --root or --preix was provided, and if
    # setuptools is not located in them, we don't patch it
    if not _under_prefix(setuptools_location):
        log.warn('Not patching, --root or --prefix is installing Distribute'
                 ' in another location')
        return

    # let's see if its an egg
    if not setuptools_location.endswith('.egg'):
        log.warn('Non-egg installation')
        res = _remove_flat_installation(setuptools_location)
        if not res:
            return
    else:
        log.warn('Egg installation')
        pkg_info = os.path.join(setuptools_location, 'EGG-INFO', 'PKG-INFO')
        if (os.path.exists(pkg_info) and
            _same_content(pkg_info, SETUPTOOLS_PKG_INFO)):
            log.warn('Already patched.')
            return
        log.warn('Patching...')
        # let's create a fake egg replacing setuptools one
        res = _patch_egg_dir(setuptools_location)
        if not res:
            return
    log.warn('Patched done.')
    _relaunch()

def _relaunch():
    log.warn('Relaunching...')
    # we have to relaunch the process
    args = [sys.executable]  + sys.argv
    if is_jython:
        sys.exit(subprocess.call(args))
    else:
        sys.exit(os.spawnv(os.P_WAIT, sys.executable, args))

import tempfile
import tarfile

def extractall(self, path=".", members=None):
        """Extract all members from the archive to the current working
           directory and set owner, modification time and permissions on
           directories afterwards. `path' specifies a different directory
           to extract to. `members' is optional and must be a subset of the
           list returned by getmembers().
        """
        import copy
        import operator
        from tarfile import ExtractError
        directories = []

        if members is None:
            members = self

        for tarinfo in members:
            if tarinfo.isdir():
                # Extract directories with a safe mode.
                directories.append(tarinfo)
                tarinfo = copy.copy(tarinfo)
                tarinfo.mode = 0700
            self.extract(tarinfo, path)

        # Reverse sort directories.
        directories.sort(key=operator.attrgetter('name'))
        directories.reverse()

        # Set correct owner, mtime and filemode on directories.
        for tarinfo in directories:
            dirpath = os.path.join(path, tarinfo.name)
            try:
                self.chown(tarinfo, dirpath)
                self.utime(tarinfo, dirpath)
                self.chmod(tarinfo, dirpath)
            except ExtractError, e:
                if self.errorlevel > 1:
                    raise
                else:
                    self._dbg(1, "tarfile: %s" % e)

def main(argv, version=DEFAULT_VERSION):
    """Install or upgrade setuptools and EasyInstall"""
    tarball = download_setuptools()
    _install(tarball)

if __name__ == '__main__':
    main(sys.argv[1:])

