import os
import re

#requires python >= 2.4
from subprocess import Popen as _Popen, PIPE as _PIPE


def get_entries_files(base, recurse=True):
    for base,dirs,files in os.walk(os.curdir):
        if '.svn' not in dirs:
            dirs[:] = []
            continue    # no sense walking uncontrolled subdirs
        dirs.remove('.svn')
        f = open(os.path.join(base,'.svn','entries'))
        yield f.read()
        f.close()

class SVNEntries(object):
    known_svn_versions = {
        '1.4.x': 8,
        '1.5.x': 9,
        '1.6.x': 10,
        #11 didn't exist (maybe 1.7-dev)
        #12 is the number in the file there is another
        #number in .svn/wb.db that is at larger so
        #looks like they won't be updating it any longer.
        '1.7.x+': 12,
        }

    def __init__(self, data):
        self.data = data

    @classmethod
    def load(class_, base):
        filename = os.path.join(base, '.svn', 'entries')
        f = open(filename)
        result = SVNEntries.read(f)
        f.close()
        return result

    @classmethod
    def read(class_, file):
        data = file.read()

        if data.startswith('<?xml'):
            #entries were originally xml so pre-1.4.x
            return SVNEntriesXML(data)
        else:
            try:
                eol = data.index('\n')
                svn_version = int(data[:eol])
                data = data[eol+1:]  # remove the revision number and newline
            except ValueError:
                log.warn('Unable to parse SVN entries file starting with %r' % data[:20])
                svn_version = None

            version_known = svn_version in class_.known_svn_versions
            if version_known and svn_version <= 10:
                return SVNEntriesText(data)
            else:
                if not version_known:
                    log.warn("Unknown subversion verson %d", svn_version)
                class_ = SVNEntriesCmd

        return class_(data)

    def parse_revision(self):
        all_revs = self.parse_revision_numbers() + [0]
        return max(all_revs)

class SVNEntriesText(SVNEntries):

    def __get_cached_sections(self):
        return self.sections
        
    def get_sections(self):
        SECTION_DIVIDER = '\f\n'
        sections = self.data.split(SECTION_DIVIDER)
        self.sections = map(str.splitlines, sections)
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
        urlre = re.compile('url="([^"]+)"')
        return urlre.search(self.data).group(1)

    def parse_revision_numbers(self):
        revre = re.compile('committed-rev="(\d+)"')
        return [
            int(m.group(1))
            for m in revre.finditer(self.data)
            ]
    
    def get_undeleted_records(self):
        entries_pattern = re.compile(r'name="([^"]+)"(?![^>]+deleted="true")', re.I)
        results = [
            unescape(match.group(1))
            for match in entries_pattern.finditer(self.data)
            ]
        return results


class SVNEntriesCMD(SVNEntries):
    entrypathre = re.compile(r'<entry\s+[^>]*path="(\.+)">', re.I)
    entryre = re.compile(r'<entry.*?</entry>', re.M or re.I)
    urlre = re.compile('<root>(.*?)</root>', re.I)
    revre = re.compile('<commit\s+[^>]*revision="(\d+)"', re.I)
    namere = re.compile('<name>(.*?)</name>', re.I)

    def __get_cached_dir_data(self):
        return self.dir_data

    def __get_cached_entries(self):
        return self.entries

    def is_valid(self):
        return bool(self.get_dir_data())

    def get_dir_data(self):
        #regard the shell argument, see: http://bugs.python.org/issue8557
        #       and http://stackoverflow.com/questions/5658622/python-subprocess-popen-environment-path
        proc = _Popen(['svn', 'info', '--xml', self.path], 
                      stdout=_PIPE, shell=(sys.platform=='win32'))
        data =  unicode(proc.communicate()[0], encoding='utf-8')
        self.dir_data = self.entryre.findall(data)
        self.get_dir_data = self.__get_cached_dir_data
        return self.dir_data

    def get_entries(self):
        #regard the shell argument, see: http://bugs.python.org/issue8557
        #       and http://stackoverflow.com/questions/5658622/python-subprocess-popen-environment-path
        proc = _Popen(['svn', 'list', '--xml', self.path], 
                      stdout=_PIPE, shell=(sys.platform=='win32'))
        data =  unicode(proc.communicate()[0], encoding='utf-8')
        self.dir_data = self.entryre.findall(data)
        self.get_dir_data = self.__get_cached_dir_data
        return self.dir_data

    def get_url(self):
        "Get repository URL"
        return self.urlre.search(self.get_sections()[0]).group(1)

    def parse_revision_numbers(self):
        #NOTE: if one has recently commited, the new revision doesn't get updated until svn update
        if not self.is_valid():
            return list()
        else:
            return [
                int(m.group(1)) 
                for entry in self.get_enteries()
                for m in self.revre.finditer(entry)
            ]
    
    def get_undeleted_records(self):
        #NOTE: Need to pars enteries?
        if not self.is_valid():
            return list()
        else:
            return [
                m.group(1))
                for entry in self.get_enteries()
                for m in self.namere.finditer(entry)                
            ]

