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

#It would seem that svn info --xml and svn list --xml were fully supported by 1.3.x
#the special casing of the entry files seem to start at 1.4.x, so if we check
#for xml in entries and then fall back to the command line, this should catch everything.

class SVNEntries(object):

    def __init__(self, path, data):
        self.path = path
        self.data = data

    @classmethod
    def load(class_, base):
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
        else if path is None:
            raise ValueError('Must have path to call svn')
        else:
            return SVNEntriesCMD(data, path)

    def parse_revision(self):
        all_revs = self.parse_revision_numbers() + [0]
        return max(all_revs)

    def __get_cached_external_dirs(self):
        return self.external_dirs

    def get_external_dirs(self):
        #regard the shell argument, see: http://bugs.python.org/issue8557
        #       and http://stackoverflow.com/questions/5658622/python-subprocess-popen-environment-path
        proc = _Popen(['svn', 'propget', self.path], 
                      stdout=_PIPE, shell=(sys.platform=='win32'))
        data = unicode(proc.communicate()[0], encoding='utf-8').splitlines()
        data = [line.split() for line in data]

        # http://svnbook.red-bean.com/en/1.6/svn.advanced.externals.html
        #there appears to be three possible formats for externals since 1.5
        #but looks like we only need the local relative path names so it's just
        #2 either the first column or the last (of 2 or 3)
        index = -1
        if all("://" in line[-1] for line in data):
            index = 0
        
        self.external_dirs = [line[index] for line in data]
        return self.dir_data

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
        #NOTE: if one has recently committed, the new revision doesn't get updated until SVN update
        if not self.is_valid():
            return list()
        else:
            return [
                int(m.group(1)) 
                for entry in self.get_enteries()
                for m in self.revre.finditer(entry)
            ]
    
    def get_undeleted_records(self):
        #NOTE: Need to parse entities?
        if not self.is_valid():
            return list()
        else:
            return [
                m.group(1))
                for entry in self.get_enteries()
                for m in self.namere.finditer(entry)                
            ]

