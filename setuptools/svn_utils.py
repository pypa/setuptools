import os
import re
import sys
from distutils import log
from xml.sax.saxutils import unescape

#requires python >= 2.4
from subprocess import Popen as _Popen, PIPE as _PIPE


def get_entries_files(base, recurse=True):
    for base, dirs, _ in os.walk(os.curdir):
        if '.svn' not in dirs:
            dirs[:] = []
            continue    # no sense walking uncontrolled subdirs
        dirs.remove('.svn')
        f = open(os.path.join(base, '.svn', 'entries'))
        yield f.read()
        f.close()

#It would seem that svn info --xml and svn list --xml were fully
#supported by 1.3.x the special casing of the entry files seem to start at
#1.4.x, so if we check for xml in entries and then fall back to the command
#line, this should catch everything.

#subprocess is called several times with shell=(sys.platform=='win32')
#see the follow for more information:
#       http://bugs.python.org/issue8557
#       http://stackoverflow.com/questions/5658622/
#              python-subprocess-popen-environment-path


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
        proc = _Popen(['svn', '--version', '--quiet'],
                      stdout=_PIPE, shell=(sys.platform=='win32'))
        data = unicode(proc.communicate()[0], encoding='utf-8')
        if data:
            return data.strip()
        else:
            return ''

    @classmethod
    def load_dir(class_, base):
        filename = os.path.join(base, '.svn', 'entries')
        f = open(filename)
        result = SVNEntries.read(f, None)
        f.close()
        return result

    @classmethod
    def read(class_, file, path=None):
        data = file.read()

        if data.startswith('<?xml'):
            #entries were originally xml so pre-1.4.x
            return SVNEntriesXML(data, path)
        elif path is None:
            return SVNEntriesText(data, path)
        else:
            class_.svn_tool_version = class_.get_svn_tool_version()
            result = SVNEntriesText(data, path)
            if result.is_valid():
                return SVNEntriesCMD(data, path)
            else:
                return result

    def parse_revision(self):
        all_revs = self.parse_revision_numbers() + [0]
        return max(all_revs)

    def __get_cached_external_dirs(self):
        return self.external_dirs

    def __get_externals_data(self, filename):
        found = False
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
        data = self.__get_externals_data(filename)

        if not data:
            return

        # http://svnbook.red-bean.com/en/1.6/svn.advanced.externals.html
        #there appears to be three possible formats for externals since 1.5
        #but looks like we only need the local relative path names so it's just
        #2 either the first column or the last (of 2 or 3) Looks like
        #mix and matching is allowed.
        data = list()
        for line in data:
            line = line.split()
            if not line:
                continue

            #TODO: urlparse?
            if "://" in line[-1] or ":\\\\" in line[-1]:
                data.append(line[-1])
            else:
                data.append(line[0])

        self.external_dirs = data
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
        SECTION_DIVIDER = '\f\n' # or '\n\x0c\n'?
        sections = self.data.split(SECTION_DIVIDER)
        sections = [section.splitlines() for section in sections]
        try:
            # remove the SVN version number from the first line
            svn_version = int(sections[0].pop(0))
            if not svn_version in self.known_svn_versions.values():
                log.warn("Unknown subversion verson %d", svn_version)
        except ValueError:
            return
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


class SVNEntriesCMD(SVNEntries):
    entrypathre = re.compile(r'<entry\s+[^>]*path="(\.+)">', re.I)
    entryre = re.compile(r'<entry.*?</entry>', re.M or re.I)
    urlre = re.compile(r'<root>(.*?)</root>', re.I)
    revre = re.compile(r'<commit\s+[^>]*revision="(\d+)"', re.I)
    namere = re.compile(r'<name>(.*?)</name>', re.I)

    def __get_cached_dir_data(self):
        return self.dir_data

    def __get_cached_entries(self):
        return self.entries

    def is_valid(self):
        return bool(self.get_dir_data())

    def get_dir_data(self):
        #regarding the shell argument, see: http://bugs.python.org/issue8557
        proc = _Popen(['svn', 'info', '--xml', self.path],
                      stdout=_PIPE, shell=(sys.platform=='win32'))
        data =  unicode(proc.communicate()[0], encoding='utf-8')
        self.dir_data = self.entryre.findall(data)
        self.get_dir_data = self.__get_cached_dir_data
        return self.dir_data

    def get_entries(self):
        #regarding the shell argument, see: http://bugs.python.org/issue8557
        proc = _Popen(['svn', 'list', '--xml', self.path],
                      stdout=_PIPE, shell=(sys.platform=='win32'))
        data =  unicode(proc.communicate()[0], encoding='utf-8')
        self.entries = self.entryre.findall(data)
        self.get_dir_data = self.__get_cached_dir_data
        return self.entries

    def get_url(self):
        "Get repository URL"
        return self.urlre.search(self.get_entries()[0]).group(1)

    def parse_revision_numbers(self):
        #NOTE: if one has recently committed,
        #      the new revision doesn't get updated until SVN update
        if not self.is_valid():
            return list()
        else:
            return [
                int(m.group(1))
                for entry in self.get_enries()
                for m in self.revre.finditer(entry)
                if m.group(1)
            ]

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

    def __get_externals_data(self, filename):

        #othewise will be called twice.
        if filename.lower() != 'dir-props':
            return ''

        #regard the shell argument, see: http://bugs.python.org/issue8557
        proc = _Popen(['svn', 'propget', self.path],
                  stdout=_PIPE, shell=(sys.platform=='win32'))
        try:
            return unicode(proc.communicate()[0], encoding='utf-8').splitlines()
        except ValueError:
            return ''
