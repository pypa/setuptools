import os
import re

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
        is_xml = data.startswith('<?xml')
        class_ = [SVNEntriesText, SVNEntriesXML][is_xml]
        return class_(data)

    def parse_revision(self):
        all_revs = self.parse_revision_numbers() + [0]
        return max(all_revs)

class SVNEntriesText(SVNEntries):
    known_svn_versions = {
        '1.4.x': 8,
        '1.5.x': 9,
        '1.6.x': 10,
        }

    def __get_cached_sections(self):
        return self.sections
        
    def get_sections(self):
        SECTION_DIVIDER = '\f\n'
        sections = self.data.split(SECTION_DIVIDER)
        sections = map(str.splitlines, sections)
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

