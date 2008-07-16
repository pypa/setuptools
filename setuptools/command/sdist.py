from distutils.command.sdist import sdist as _sdist
from distutils.util import convert_path
from distutils import log
import os, re, sys, pkg_resources

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










def walk_revctrl(dirname=''):
    """Find all files under revision control"""
    for ep in pkg_resources.iter_entry_points('setuptools.file_finders'):
        for item in ep.load()(dirname):
            yield item

def _default_revctrl(dirname=''):
    for path, finder in finders:
        path = joinpath(dirname,path)
        if os.path.isfile(path):
            for path in finder(dirname,path):
                if os.path.isfile(path):
                    yield path
                elif os.path.isdir(path):
                    for item in _default_revctrl(path):
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


entries_pattern = re.compile(r'name="([^"]+)"(?![^>]+deleted="true")', re.I)

def entries_finder(dirname, filename):
    f = open(filename,'rU')
    data = f.read()
    f.close()
    if data.startswith('9') or data.startswith('8'):    # subversion 1.5/1.4
        for record in map(str.splitlines, data.split('\n\x0c\n')[1:]):
            if not record or len(record)>=6 and record[5]=="delete":
                continue    # skip deleted
            yield joinpath(dirname, record[0])
    elif data.startswith('<?xml'):
        for match in entries_pattern.finditer(data):
            yield joinpath(dirname,unescape(match.group(1)))
    else:
        log.warn("unrecognized .svn/entries format in %s", dirname)


finders = [
    (convert_path('CVS/Entries'),
        re_finder(re.compile(r"^\w?/([^/]+)/", re.M))),
    (convert_path('.svn/entries'), entries_finder),
    (convert_path('.svn/dir-props'), externals_finder),
    (convert_path('.svn/dir-prop-base'), externals_finder),  # svn 1.4
]
















class sdist(_sdist):
    """Smart sdist that finds anything supported by revision control"""

    user_options = [
        ('formats=', None,
         "formats for source distribution (comma-separated list)"),
        ('keep-temp', 'k',
         "keep the distribution tree around after creating " +
         "archive file(s)"),
        ('dist-dir=', 'd',
         "directory to put the source distribution archive(s) in "
         "[default: dist]"),
        ]

    negative_opt = {}

    def run(self):
        self.run_command('egg_info')
        ei_cmd = self.get_finalized_command('egg_info')
        self.filelist = ei_cmd.filelist
        self.filelist.append(os.path.join(ei_cmd.egg_info,'SOURCES.txt'))
        self.check_readme()
        self.check_metadata()
        self.make_distribution()

        dist_files = getattr(self.distribution,'dist_files',[])
        for file in self.archive_files:
            data = ('sdist', '', file)
            if data not in dist_files:
                dist_files.append(data)

    def read_template(self):
        try:
            _sdist.read_template(self)
        except:
            # grody hack to close the template file (MANIFEST.in)
            # this prevents easy_install's attempt at deleting the file from
            # dying and thus masking the real error
            sys.exc_info()[2].tb_next.tb_frame.f_locals['template'].close()
            raise

    def check_readme(self):
        alts = ("README", "README.txt")
        for f in alts:
            if os.path.exists(f):
                return
        else:
            self.warn(
                "standard file not found: should have one of " +', '.join(alts)
            )


    def make_release_tree(self, base_dir, files):
        _sdist.make_release_tree(self, base_dir, files)

        # Save any egg_info command line options used to create this sdist
        dest = os.path.join(base_dir, 'setup.cfg')
        if hasattr(os,'link') and os.path.exists(dest):
            # unlink and re-copy, since it might be hard-linked, and
            # we don't want to change the source version
            os.unlink(dest)
            self.copy_file('setup.cfg', dest)

        self.get_finalized_command('egg_info').save_version_info(dest)

















#
