import os
import re
import sys
from distutils import log
import xml.dom.pulldom
import shlex
import locale
import unicodedata
from setuptools.compat import unicode, bytes

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from subprocess import Popen as _Popen, PIPE as _PIPE

#NOTE: Use of the command line options require SVN 1.3 or newer (December 2005)
#      and SVN 1.3 hasn't been supported by the developers since mid 2008.

#subprocess is called several times with shell=(sys.platform=='win32')
#see the follow for more information:
#       http://bugs.python.org/issue8557
#       http://stackoverflow.com/questions/5658622/
#              python-subprocess-popen-environment-path
def _run_command(args, stdout=_PIPE, stderr=_PIPE):
    #regarding the shell argument, see: http://bugs.python.org/issue8557
    try:
        args = [fsdecode(x) for x in args]
        proc = _Popen(args, stdout=stdout, stderr=stderr,
                      shell=(sys.platform == 'win32'))

        data = proc.communicate()[0]
    except OSError:
        return 1, ''

    data = consoledecode(data)

    #communciate calls wait()
    return proc.returncode, data


def _get_entry_schedule(entry):
    schedule = entry.getElementsByTagName('schedule')[0]
    return "".join([t.nodeValue
                    for t in schedule.childNodes
                    if t.nodeType == t.TEXT_NODE])


def _get_target_property(target):
    property_text = target.getElementsByTagName('property')[0]
    return "".join([t.nodeValue
                    for t in property_text.childNodes
                    if t.nodeType == t.TEXT_NODE])


def _get_xml_data(decoded_str):
    if sys.version_info < (3, 0):
        #old versions want an encoded string
        data = decoded_str.encode('utf-8')
    else:
        data = decoded_str
    return data


def joinpath(prefix, suffix):
    if not prefix or prefix == '.':
        return suffix
    return os.path.join(prefix, suffix)


def fsencode(path):
    "Path must be unicode or in file system encoding already"
    encoding = sys.getfilesystemencoding()

    if isinstance(path, unicode):
        path = path.encode()
    elif not isinstance(path, bytes):
        raise TypeError('%s is not a string or byte type'
                        % type(path).__name__)

    #getfilessystemencoding doesn't have the mac-roman issue
    if encoding == 'utf-8' and sys.platform == 'darwin':
        path = path.decode('utf-8')
        path = unicodedata.normalize('NFD', path)
        path = path.encode('utf-8')

    return path

def fsdecode(path):
    "Path must be unicode or in file system encoding already"
    encoding = sys.getfilesystemencoding()
    if isinstance(path, bytes):
        path = path.decode(encoding)
    elif not isinstance(path, unicode):
        raise TypeError('%s is not a byte type'
                        % type(path).__name__)

    return unicodedata.normalize('NFC', path)

def consoledecode(text):
    encoding = locale.getpreferredencoding()
    return text.decode(encoding)


def parse_dir_entries(decoded_str):
    '''Parse the entries from a recursive info xml'''
    doc = xml.dom.pulldom.parseString(_get_xml_data(decoded_str))
    entries = list()

    for event, node in doc:
        if event == 'START_ELEMENT' and node.nodeName == 'entry':
            doc.expandNode(node)
            if not _get_entry_schedule(node).startswith('delete'):
                entries.append((node.getAttribute('path'),
                                node.getAttribute('kind')))

    return entries[1:]  # do not want the root directory


def parse_externals_xml(decoded_str, prefix=''):
    '''Parse a propget svn:externals xml'''
    prefix = os.path.normpath(prefix)
    prefix = os.path.normcase(prefix)

    doc = xml.dom.pulldom.parseString(_get_xml_data(decoded_str))
    externals = list()

    for event, node in doc:
        if event == 'START_ELEMENT' and node.nodeName == 'target':
            doc.expandNode(node)
            path = os.path.normpath(node.getAttribute('path'))
            log.warn('')
            log.warn('PRE: %s' % prefix)
            log.warn('PTH: %s' % path)
            if os.path.normcase(path).startswith(prefix):
                path = path[len(prefix)+1:]

            data = _get_target_property(node)
            for external in parse_external_prop(data):
                externals.append(joinpath(path, external))

    return externals  # do not want the root directory


def parse_external_prop(lines):
    """
    Parse the value of a retrieved svn:externals entry.

    possible token setups (with quotng and backscaping in laters versions)
        URL[@#] EXT_FOLDERNAME
        [-r#] URL EXT_FOLDERNAME
        EXT_FOLDERNAME [-r#] URL
    """
    externals = []
    for line in lines.splitlines():
        line = line.lstrip() #there might be a "\ "
        if not line:
            continue

        if sys.version_info < (3, 0):
            #shlex handles NULLs just fine and shlex in 2.7 tries to encode
            #as ascii automatiically
            line = line.encode('utf-8')
        line = shlex.split(line)
        if sys.version_info < (3, 0):
            line = [x.decode('utf-8') for x in line]

        #EXT_FOLDERNAME is either the first or last depending on where
        #the URL falls
        if urlparse.urlsplit(line[-1])[0]:
            external = line[0]
        else:
            external = line[-1]

        externals.append(os.path.normpath(external))

    return externals


class SvnInfo(object):
    '''
    Generic svn_info object.  No has little knowledge of how to extract
    information.  Use cls.load to instatiate according svn version.

    Paths are not filesystem encoded.
    '''

    @staticmethod
    def get_svn_version():
        code, data = _run_command(['svn', '--version', '--quiet'])
        if code == 0 and data:
            return unicode(data).strip()
        else:
            return unicode('')

    #svnversion return values (previous implementations return max revision)
    #   4123:4168     mixed revision working copy
    #   4168M         modified working copy
    #   4123S         switched working copy
    #   4123:4168MS   mixed revision, modified, switched working copy
    revision_re = re.compile(r'(?:([\-0-9]+):)?(\d+)([a-z]*)\s*$', re.I)

    @classmethod
    def load(cls, dirname=''):
        code, data = _run_command(['svn', 'info', os.path.normpath(dirname)])
        svn_version = tuple(cls.get_svn_version().split('.'))
        base_svn_version = tuple(int(x) for x in svn_version[:2])
        if code and base_svn_version:
            #Not an SVN repository or compatible one
            return SvnInfo(dirname)
        elif base_svn_version < (1, 3):
            log.warn('Insufficent version of SVN found')
            return SvnInfo(dirname)
        elif base_svn_version < (1, 5):
            return Svn13Info(dirname)
        else:
            return Svn15Info(dirname)

    def __init__(self, path=''):
        self.path = path
        self._entries = None
        self._externals = None

    def get_revision(self):
        'Retrieve the directory revision informatino using svnversion'
        code, data = _run_command(['svnversion', '-c', self.path])
        if code:
            log.warn("svnversion failed")
            return 0

        parsed = self.revision_re.match(data)
        if parsed:
            return int(parsed.group(2))
        else:
            return 0

    @property
    def entries(self):
        if self._entries is None:
            self._entries = self.get_entries()
        return self._entries

    @property
    def externals(self):
        if self._externals is None:
            self._externals = self.get_externals()
        return self._externals

    def iter_externals(self):
        '''
        Iterate over the svn:external references in the repository path.
        '''
        for item in self.externals:
            yield item

    def iter_files(self):
        '''
        Iterate over the non-deleted file entries in the repository path
        '''
        for item, kind in self.entries:
            if kind.lower()=='file':
                yield item

    def iter_dirs(self, include_root=True):
        '''
        Iterate over the non-deleted file entries in the repository path
        '''
        if include_root:
            yield self.path
        for item, kind in self.entries:
            if kind.lower()=='dir':
                yield item

    def get_entries(self):
        return []

    def get_externals(self):
        return []

class Svn13Info(SvnInfo):
    def get_entries(self):
        code, data = _run_command(['svn', 'info', '-R', '--xml', self.path])

        if code:
            log.debug("svn info failed")
            return []

        return parse_dir_entries(data)

    def get_externals(self):
        #Previous to 1.5 --xml was not supported for svn propget and the -R
        #output format breaks the shlex compatible semantics.
        cmd = ['svn', 'propget', 'svn:externals']
        result = []
        for folder in self.iter_dirs():
            code, lines = _run_command(cmd + [folder])
            if code != 0:
                log.warn("svn propget failed")
                return []
            for external in parse_external_prop(lines):
                if folder:
                    external = os.path.join(folder, external)
                result.append(os.path.normpath(external))

        return result


class Svn15Info(Svn13Info):
    def get_externals(self):
        cmd = ['svn', 'propget', 'svn:externals', self.path, '-R', '--xml']
        code, lines = _run_command(cmd)
        if code:
            log.debug("svn propget failed")
            return []
        return parse_externals_xml(lines, prefix=os.path.abspath(self.path))


def svn_finder(dirname=''):
    #combined externals due to common interface
    #combined externals and entries due to lack of dir_props in 1.7
    info = SvnInfo.load(dirname)
    for path in info.iter_files():
        yield fsencode(path)

    for path in info.iter_externals():
        sub_info = SvnInfo.load(path)
        for sub_path in sub_info.iter_files():
            yield fsencode(sub_path)

if __name__ == '__main__':
    for name in svn_finder(sys.argv[1]):
        print(name)