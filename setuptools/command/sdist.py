from distutils.command.sdist import sdist as _sdist
from distutils.util import convert_path
import os,re

entities = [
    ("&lt;","<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'"),
    ("&amp;", "&")
]

def unescape(data):
    for old,new in entities:
        data = data.replace(old,new)
    return data

def re_finder(pattern, postproc=None):
    def find(dirname, filename):
        f = open(filename,'rU')
        data = f.read()
        f.close()
        for match in pattern.finditer(data):
            path = match.group(1)
            if postproc:
                path = postproc(path)
            yield joinpath(dirname,path)
    return find

def joinpath(prefix,suffix):
    if not prefix:
        return suffix
    return os.path.join(prefix,suffix)











def walk_revctrl(dirname='', memo=None):
    """Find all files under revision control"""
    if memo is None:
        memo = {}
    if dirname in memo:
        # Don't rescan a scanned directory
        return
    for path, finder in finders:
        path = joinpath(dirname,path)
        if os.path.isfile(path):
            for path in finder(dirname,path):
                if os.path.isfile(path):
                    yield path
                elif os.path.isdir(path):
                    for item in walk_revctrl(path, memo):
                        yield item

def externals_finder(dirname, filename):
    """Find any 'svn:externals' directories"""
    found = False
    f = open(filename,'rb')
    for line in iter(f.readline, ''):    # can't use direct iter!
        parts = line.split()
        if len(parts)==2:
            kind,length = parts
            data = f.read(int(length))
            if kind=='K' and data=='svn:externals':
                found = True
            elif kind=='V' and found:
                f.close()
                break
    else:
        f.close()
        return

    for line in data.splitlines():
        parts = line.split()
        if parts:
            yield joinpath(dirname, parts[0])


finders = [
    (convert_path('CVS/Entries'),
        re_finder(re.compile(r"^\w?/([^/]+)/", re.M))),
    (convert_path('.svn/entries'),
        re_finder(re.compile(r'name="([^"]+)"'), unescape)),
    (convert_path('.svn/dir-props'), externals_finder),
]


class sdist(_sdist):
    """Smart sdist that finds anything supported by revision control"""

    def run(self):
        self.run_command('egg_info')
        _sdist.run(self)
        dist_files = getattr(self.distribution,'dist_files',[])
        for file in self.archive_files:
            data = ('sdist', '', file)
            if data not in dist_files:
                dist_files.append(data)

    def finalize_options(self):
        _sdist.finalize_options(self)
        if not os.path.isfile(self.template):
            self.force_manifest = 1     # always regen if no template

    def add_defaults(self):
        _sdist.add_defaults(self)
        self.filelist.extend(walk_revctrl())












