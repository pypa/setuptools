import os
import zipfile
import sys
import tempfile
import unittest
import shutil
import stat
import unicodedata

from subprocess import Popen as _Popen, PIPE as _PIPE


def _remove_dir(target):

    #on windows this seems to a problem
    for dir_path, dirs, files in os.walk(target):
        os.chmod(dir_path, stat.S_IWRITE)
        for filename in files:
            os.chmod(os.path.join(dir_path, filename), stat.S_IWRITE)
    shutil.rmtree(target)


class ZippedEnvironment(unittest.TestCase):

    datafile = None
    dataname = None
    old_cwd = None

    def setUp(self):
        if self.datafile is None or self.dataname is None:
            return

        if not os.path.isfile(self.datafile):
            self.old_cwd = None
            return

        self.old_cwd = os.getcwd()

        self.temp_dir = tempfile.mkdtemp()
        zip_file, source, target = [None, None, None]
        try:
            zip_file = zipfile.ZipFile(self.datafile)
            for files in zip_file.namelist():
                zip_file.extract(files, self.temp_dir)
        finally:
            if zip_file:
                zip_file.close()
            del zip_file

        os.chdir(os.path.join(self.temp_dir, self.dataname))

    def tearDown(self):
        #Assume setUp was never completed
        if self.dataname is None or self.datafile is None:
            return

        try:
            if self.old_cwd:
                os.chdir(self.old_cwd)
                _remove_dir(self.temp_dir)
        except OSError:
            #sigh?
            pass


def _which_dirs(cmd):
    result = set()
    for path in os.environ.get('PATH', '').split(os.pathsep):
        filename = os.path.join(path, cmd)
        if os.access(filename, os.X_OK):
            result.add(path)
    return result


def run_setup_py(cmd, pypath=None, path=None,
                 data_stream=0, env=None):
    """
    Execution command for tests, separate from those used by the
    code directly to prevent accidental behavior issues
    """
    if env is None:
        env = dict()
        for envname in os.environ:
            env[envname] = os.environ[envname]

    #override the python path if needed
    if pypath is not None:
        env["PYTHONPATH"] = pypath

    #overide the execution path if needed
    if path is not None:
        env["PATH"] = path
    if not env.get("PATH", ""):
        env["PATH"] = _which_dirs("tar").union(_which_dirs("gzip"))
        env["PATH"] = os.pathsep.join(env["PATH"])

    cmd = [sys.executable, "setup.py"] + list(cmd)

    # http://bugs.python.org/issue8557
    shell = sys.platform == 'win32'

    try:
        proc = _Popen(
            cmd, stdout=_PIPE, stderr=_PIPE, shell=shell, env=env,
        )

        data = proc.communicate()[data_stream]
    except OSError:
        return 1, ''

    #decode the console string if needed
    if hasattr(data,  "decode"):
        # use the default encoding
        data = data.decode()
        data = unicodedata.normalize('NFC', data)

    #communciate calls wait()
    return proc.returncode, data
