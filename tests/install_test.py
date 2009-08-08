import urllib2
import sys
import os

if os.path.exists('distribute_setup.py'):
    print 'distribute_setup.py exists in the current dir, aborting'
    sys.exit(2)

print '**** Starting Test'
print '\n\n'

is_jython = sys.platform.startswith('java')
if is_jython:
    import subprocess

print 'Downloading bootstrap'
file = urllib2.urlopen('http://nightly.ziade.org/distribute_setup.py')
f = open('distribute_setup.py', 'w')
f.write(file.read())
f.close()

# running it
args = [sys.executable]  + ['distribute_setup.py']
if is_jython:
    res = subprocess.call(args)
else:
    res = os.spawnv(os.P_WAIT, sys.executable, args)

if res != 0:
    print '**** Test failed, please send me the output at tarek@ziade.org'
    os.remove('distribute_setup.py')
    sys.exit(2)

# now checking if Distribute is installed
script = """\
import sys
try:
    import setuptools
except ImportError:
    sys.exit(0)

sys.exit(hasattr(setuptools, "_distribute"))
"""

root = 'script'
seed = 0
script_name = '%s%d.py' % (root, seed)

while os.path.exists(script_name):
    seed += 1
    script_name = '%s%d.py' % (root, seed)

f = open(script_name, 'w')
try:
    f.write(script)
finally:
    f.close()

try:
    args = [sys.executable]  + [script_name]
    if is_jython:
        res = subprocess.call(args)
    else:
        res = os.spawnv(os.P_WAIT, sys.executable, args)

    print '\n\n'
    if res:
        print '**** Test is OK'
    else:
        print '**** Test failed, please send me the output at tarek@ziade.org'
finally:
    if os.path.exists(script_name):
        os.remove(script_name)
    os.remove('distribute_setup.py')

