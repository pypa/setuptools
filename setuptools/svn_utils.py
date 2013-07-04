import os
import re
import sys
import codecs
from distutils import log
from xml.sax.saxutils import unescape
import xml.dom.pulldom

#requires python >= 2.4
from subprocess import Popen as _Popen, PIPE as _PIPE


#It would seem that svn info --xml and svn list --xml were fully
#supported by 1.3.x the special casing of the entry files seem to start at
#1.4.x, so if we check for xml in entries and then fall back to the command
#line, this should catch everything.

#subprocess is called several times with shell=(sys.platform=='win32')
#see the follow for more information:
#       http://bugs.python.org/issue8557
#       http://stackoverflow.com/questions/5658622/
#              python-subprocess-popen-environment-path
def _run_command(args, stdout=_PIPE, stderr=_PIPE):
        #regarding the shell argument, see: http://bugs.python.org/issue8557
        proc = _Popen(args, stdout=stdout, stderr=stderr,
                      shell=(sys.platform=='win32'))

        data = proc.communicate()[0]
        #TODO: this is probably NOT always utf-8
        try:
            data = unicode(data, encoding='utf-8')
        except NameError:
            data = str(data, encoding='utf-8')

        return proc.returncode, data

#svnversion return values (previous implementations return max revision)
#   4123:4168     mixed revision working copy
#   4168M         modified working copy
#   4123S         switched working copy
#   4123:4168MS   mixed revision, modified, switched working copy
_SVN_VER_RE = re.compile(r'(?:(\d+):)?(\d+)([a-z]*)\s*$', re.I)

def parse_revision(path):
    _, data = _run_command(['svnversion', path])
    parsed = _SVN_VER_RE.match(data)
    if parsed:
        try:
            #No max needed this command summarizes working copy since 1.0
            return int(parsed.group(2))
        except ValueError:
            #This should only happen if the revision is WAY too big.
            pass
    return 0

#TODO add the text entry back, and make its use dependent on the
#     non existence of svn?

class SVNEntries(object):
    svn_tool_version = ''

    def __init__(self, path, data):
        self.path = path
        self.data = data
        if not self.svn_tool_version:
            self.svn_tool_version = self.get_svn_tool_version()

    @staticmethod
    def get_svn_tool_version():
        _, data = _run_command(['svn', '--version', '--quiet'])
        if data:
            return data.strip()
        else:
            return ''

    @classmethod
    def load_dir(class_, base):
        filename = os.path.join(base, '.svn', 'entries')
        f = open(filename)
        result = SVNEntries.read(f, base)
        f.close()
        return result

    @classmethod
    def read(class_, file, path=None):
        data = file.read()

        if data.startswith('<?xml'):
            #entries were originally xml so pre-1.4.x
            return SVNEntriesXML(path, data)
        elif path is None:
            return SVNEntriesText(path, data)
        else:
            result = SVNEntriesText(path, data)
            if result.is_valid():
                return result
            else:
                return SVNEntriesCMD(path, data)

    def parse_revision(self):
        all_revs = self.parse_revision_numbers() + [0]
        return max(all_revs)

    def __get_cached_external_dirs(self):
        return self.external_dirs

    def _get_externals_data(self, filename):
        found = False
        if not os.path.isfile(filename):
            return

        f = open(filename,'rt')
        for line in iter(f.readline, ''):    # can't use direct iter!
            parts = line.split()
            if len(parts)==2:
                kind, length = parts
                data = f.read(int(length))
                if kind == 'K' and data == 'svn:externals':
                    found = True
                elif kind == 'V' and found:
                    f.close()
                    break
        else:
            f.close()
            return ''

    def get_external_dirs(self, filename):
        filename = os.path.join(self.path, '.svn', filename)

        data = self._get_externals_data(filename)

        if not data:
            return

        # http://svnbook.red-bean.com/en/1.6/svn.advanced.externals.html
        #there appears to be three possible formats for externals since 1.5
        #but looks like we only need the local relative path names so it's just
        #2 either the first column or the last (of 2 or 3) Looks like
        #mix and matching is allowed.
        externals = list()
        for line in data:
            line = line.split()
            if not line:
                continue

            #TODO: urlparse?
            if "://" in line[-1] or ":\\\\" in line[-1]:
                externals.append(line[0])
            else:
                externals.append(line[-1])

        self.external_dirs = externals
        self.get_external_dirs = self.__get_cached_external_dirs
        return self.external_dirs

class SVNEntriesText(SVNEntries):
    known_svn_versions = {
        '1.4.x': 8,
        '1.5.x': 9,
        '1.6.x': 10,
        }

    def __get_cached_sections(self):
        return self.sections

    def get_sections(self):
        # remove the SVN version number from the first line
        svn_version, _, sections = self.data.partition("\n")
        try:
            svn_version = int(svn_version)
            if not svn_version in self.known_svn_versions.values():
                log.warn("SVNEntriesText: Unknown subversion verson %d."
                         "  Maybe another parser will work,", svn_version)
        except ValueError:
            return

        SECTION_DIVIDER = '\f\n' # or '\n\x0c\n'?
        sections = sections.split(SECTION_DIVIDER)
        sections = [section.splitlines() for section in sections if section]

        self.sections = sections
        self.get_sections = self.__get_cached_sections
        return self.sections

    def is_valid(self):
        return bool(self.get_sections())

    def get_url(self):
        return self.get_sections()[0][4]

    def parse_revision_numbers(self):
        revision_line_number = 9
        rev_numbers = [
            int(section[revision_line_number])
            for section in self.get_sections()
            if len(section)>revision_line_number
                and section[revision_line_number]
            ]
        return rev_numbers

    def get_undeleted_records(self):
        #Note for self this skip and only returns the children
        undeleted = lambda s: s and s[0] and (len(s) < 6 or s[5] != 'delete')
        result = [
            section[0]
            for section in self.get_sections()
            if undeleted(section)
            ]
        return result


class SVNEntriesXML(SVNEntries):
    def is_valid(self):
        return True

    def get_url(self):
        "Get repository URL"
        urlre = re.compile(r'url="([^"]+)"')
        return urlre.search(self.data).group(1)

    def parse_revision_numbers(self):
        revre = re.compile(r'committed-rev="(\d+)"')
        return [
            int(m.group(1))
            for m in revre.finditer(self.data)
            if m.group(1)
            ]

    def get_undeleted_records(self):
        entries_pattern = re.compile(r'name="([^"]+)"(?![^>]+deleted="true")',
                                     re.I)
        results = [
            unescape(match.group(1))
            for match in entries_pattern.finditer(self.data)
            if match.group(1)
            ]
        return results

import xml.dom.pulldom

class SVNEntriesCMD(SVNEntries):
    #<info>
    #  <entry path=''      //Entry Path
    #         revision=''
    #         kind=''>
    #    <url>
    #    <repository>
    #       <root>...</root>
    #       <uuid>...</uuid>
    #    </repository>
    #    <wc-info>
    #       ...
    #    </wc-info>
    #    <commit revision=''>
    #       ...
    #    </commit>
    #  </entry>
    #  ...
    #</info>
    entrypathre = re.compile(r'<entry\s+[^>]*path="(\.+)">', re.I)
    entryre = re.compile(r'<entry.*?</entry>', re.DOTALL or re.I)
    namere = re.compile(r'<name>(.*?)</name>', re.I)

    def __get_cached_dir_data(self):
        return self.dir_data

    def __get_cached_entries(self):
        return self.entries

    def is_valid(self):
        return self.get_dir_data() is not None

    def get_dir_data(self):
        #This returns the info entry for the directory ONLY
        _, data = _run_command(['svn', 'info', '--xml', self.path])

        doc = xml.dom.pulldom.parseString(data)
        self.dir_data = None
        for event, node in doc:
            if event=='START_ELEMENT' and node.nodeName=='entry':
                doc.expandNode(node)
                self.dir_data = node
                break

        if self.dir_data:
            self.get_dir_data = self.__get_cached_dir_data
        return self.dir_data

    def get_entries(self):
        #regarding the shell argument, see: http://bugs.python.org/issue8557
        _, data = _run_command(['svn', 'list', '--xml', self.path])
        self.entries = self.entryre.findall(data)
        self.get_entries = self.__get_cached_entries
        return self.entries



    def get_url(self):
        "Get repository URL"
        url_element = self.get_dir_data().getElementsByTagName("url")[0]
        url_text = [t.nodeValue for t in url_element.childNodes
                                if t.nodeType == t.TEXT_NODE]
        return "".join(url_text)

    def __get_cached_revision(self):
        return self.revision

    def parse_revision(self):
        self.revision = parse_revision(self.path)
        self.parse_revision = self.__get_cached_revision
        return self.revision

    def get_undeleted_records(self):
        #NOTE: Need to parse entities?
        if not self.is_valid():
            return list()
        else:
            return [
                m.group(1)
                for entry in self.get_entries()
                for m in self.namere.finditer(entry)
                if m.group(1)
            ]

    def _get_externals_data(self, filename):

        #othewise will be called twice.
        if os.path.basename(filename).lower() != 'dir-props':
            return ''

        try:
            _, lines = _run_command(['svn',
                                     'propget', 'svn:externals', self.path])
            lines = [line for line in lines.splitlines() if line]
            return lines
        except ValueError:
            return ''
