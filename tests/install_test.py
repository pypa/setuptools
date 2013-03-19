import urllib2
import sys
import os

bootstrap_name = 'ez_setup.py'

if os.path.exists(bootstrap_name):
    print bootstrap_name + ' exists in the current dir, aborting'
    sys.exit(2)

print '**** Starting Test'
print '\n\n'

is_jython = sys.platform.startswith('java')
if is_jython:
    import subprocess

print 'Downloading bootstrap'
file = urllib2.urlopen('https://bitbucket.org/jaraco/setuptools-private'
    '/src/tip/' + bootstrap_name)
f = open(bootstrap_name, 'w')
f.write(file.read())
f.close()

# running it
args = [sys.executable, bootstrap_name]
if is_jython:
    res = subprocess.call(args)
else:
    res = os.spawnv(os.P_WAIT, sys.executable, args)

fail_message = ('**** Test failed; please report the output to the '
    'setuptools bugtracker.')

if res != 0:
    print(fail_message)
    os.remove(bootstrap_name)
    sys.exit(2)

# now checking if Setuptools is installed
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
        print(fail_message)
finally:
    if os.path.exists(script_name):
        os.remove(script_name)
    os.remove(bootstrap_name)

