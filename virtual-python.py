"""Create a "virtual" Python installation

Based on a script created by Ian Bicking."""

import sys, os, optparse, shutil
join = os.path.join
py_version = 'python%s.%s' % (sys.version_info[0], sys.version_info[1])

def mkdir(path):
    if not os.path.exists(path):
        print 'Creating %s' % path
        os.makedirs(path)
    else:
        if verbose:
            print 'Directory %s already exists'

def symlink(src, dest):
    if not os.path.exists(dest):
        if verbose:
            print 'Creating symlink %s' % dest
        os.symlink(src, dest)
    else:
        print 'Symlink %s already exists' % dest


def rmtree(dir):
    if os.path.exists(dir):
        print 'Deleting tree %s' % dir
        shutil.rmtree(dir)
    else:
        if verbose:
            print 'Do not need to delete %s; already gone' % dir

def make_exe(fn):
    if os.name == 'posix':
        oldmode = os.stat(fn).st_mode & 07777
        newmode = (oldmode | 0555) & 07777
        os.chmod(fn, newmode)
        if verbose:
            print 'Changed mode of %s to %s' % (fn, oct(newmode))

def main():
    if os.name != 'posix':
        print "This script only works on Unix-like platforms, sorry."
        return

    parser = optparse.OptionParser()
    
    parser.add_option('-v', '--verbose', action='count', dest='verbose',
        default=0, help="Increase verbosity")
        
    parser.add_option('--prefix', dest="prefix", default='~',
        help="The base directory to install to (default ~)")
        
    parser.add_option('--clear', dest='clear', action='store_true',
        help="Clear out the non-root install and start from scratch")
        
    parser.add_option('--no-site-packages', dest='no_site_packages',
        action='store_true',
        help="Don't copy the contents of the global site-packages dir to the "
             "non-root site-packages")
    
    options, args = parser.parse_args()
    global verbose

    home_dir = os.path.expanduser(options.prefix)
    lib_dir = join(home_dir, 'lib', py_version)
    inc_dir = join(home_dir, 'include', py_version)
    bin_dir = join(home_dir, 'bin')

    if sys.executable.startswith(bin_dir):
        print 'Please use the *system* python to run this script'
        return

    verbose = options.verbose
    assert not args, "No arguments allowed"
        
    if options.clear:
        rmtree(lib_dir)
        rmtree(inc_dir)
        print 'Not deleting', bin_dir

    prefix = sys.prefix
    mkdir(lib_dir)
    stdlib_dir = join(prefix, 'lib', py_version)
    for fn in os.listdir(stdlib_dir):
        if fn != 'site-packages':
            symlink(join(stdlib_dir, fn), join(lib_dir, fn))

    mkdir(join(lib_dir, 'site-packages'))
    if not options.no_site_packages:
        for fn in os.listdir(join(stdlib_dir, 'site-packages')):
            symlink(join(stdlib_dir, 'site-packages', fn),
                    join(lib_dir, 'site-packages', fn))

    mkdir(inc_dir)
    stdinc_dir = join(prefix, 'include', py_version)
    for fn in os.listdir(stdinc_dir):
        symlink(join(stdinc_dir, fn), join(inc_dir, fn))

    if sys.exec_prefix != sys.prefix:
        exec_dir = join(sys.exec_prefix, 'lib', py_version)
        for fn in os.listdir(exec_dir):
            symlink(join(exec_dir, fn), join(lib_dir, fn))

    mkdir(bin_dir)
    print 'Copying %s to %s' % (sys.executable, bin_dir)
    py_executable = join(bin_dir, 'python')
    if sys.executable != py_executable:
        shutil.copyfile(sys.executable, py_executable)
        make_exe(py_executable)

    pydistutils = os.path.expanduser('~/.pydistutils.cfg')
    if os.path.exists(pydistutils):
        print 'Please make sure you remove any previous custom paths from'
        print "your", pydistutils, "file."

    print "You're now ready to download ez_setup.py, and run"
    print py_executable, "ez_setup.py"
      
if __name__ == '__main__':
    main()

