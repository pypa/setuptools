#!/usr/bin/env python

"""
Script to fully automate the release process. Requires Python 2.6+
with sphinx installed and the 'hg' command on the path.
"""

from __future__ import print_function

import subprocess
import shutil
import os
import sys

VERSION='0.6.25'

def get_next_version():
	digits = map(int, VERSION.split('.'))
	digits[-1] += 1
	return '.'.join(map(str, digits))

NEXT_VERSION = get_next_version()

def bump_versions():
	files_with_versions = ('docs/conf.py', 'setup.py', 'release.py',
		'release.sh', 'README.txt', 'distribute_setup.py')
	list(map(bump_version, files_with_versions))

def bump_version(filename):
	with open(filename, 'rb') as f:
		lines = [line.replace(VERSION, NEXT_VERSION) for line in f]
	with open(filename, 'wb') as f:
		f.writelines(lines)

def do_release():
	res = raw_input('Have you read through the SCM changelog and '
		'confirmed the changelog is current for releasing {VERSION}? '
		.format(**globals()))
	if not res.lower().startswith('y'):
		print("Please do that")
		raise SystemExit(1)

	res = raw_input('Have you or has someone verified that the tests '
		'pass on this revision? ')
	if not res.lower().startswith('y'):
		print("Please do that")
		raise SystemExit(2)

	subprocess.check_call(['hg', 'tag', VERSION])

	subprocess.check_call(['hg', 'update', VERSION])

	build_docs()
	if os.path.isdir('./dist'):
		shutil.rmtree('./dist')
	subprocess.check_call([sys.executable, 'setup.py',
		'-q', 'egg_info', '-RD', '-b', '', 'sdist', 'register',
		'upload', 'upload_docs'])
	upload_bootstrap_script()

	# we just tagged the current version, bump for the next release.
	bump_versions()
	subprocess.check_call(['hg', 'ci', '-m',
		'Bumped to {NEXT_VERSION} in preparation for next '
		'release.'.format(**globals())])

	# push the changes
	subprocess.check_call(['hg', 'push'])

	# TODO: update bitbucket milestones and versions

def build_docs():
	if os.path.isdir('docs/build'):
		shutil.rmtree('docs/build')
	subprocess.check_call([
		'sphinx-build',
		'-b', 'html',
		'-d', 'build/doctrees',
		'.',
		'build/html',
		],
		cwd='docs')

def upload_bootstrap_script():
	scp_command = 'pscp' if sys.platform.startswith('win') else 'scp'
	try:
		subprocess.check_call([scp_command, 'distribute_setup.py',
			'pypi@ziade.org:python-distribute.org/'])
	except:
		print("Unable to upload bootstrap script. Ask Tarek to do it.")

if __name__ == '__main__':
	do_release()
