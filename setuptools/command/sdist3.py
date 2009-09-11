import os
from distutils import log
from sdist import sdist
from lib2to3.refactor import RefactoringTool, get_fixers_from_package


class _RefactoringTool(RefactoringTool):
    def log_error(self, msg, *args, **kw):
        log.error(msg, *args)
        
    def log_message(self, msg, *args):
        log.info(msg, *args)

    def log_debug(self, msg, *args):
        log.debug(msg, *args)


class sdist3(sdist):
    description = "sdist version that runs 2to3 on all sources before packaging"
    fixer_names = None

    def copy_file(self, file, dest, link=None):
        # We ignore the link parameter, always demanding a copy, so that
        # 2to3 won't overwrite the original file.
        sdist.copy_file(self, file, dest)

    def make_release_tree(self, base_dir, files):
        sdist.make_release_tree(self, base_dir, files)

        # run 2to3 on all files
        fixer_names = self.fixer_names
        if fixer_names is None:
            fixer_names = get_fixers_from_package('lib2to3.fixes')
        r = _RefactoringTool(fixer_names)
        r.refactor([os.path.join(base_dir, f) for f in files if f.endswith(".py")], write=True)
