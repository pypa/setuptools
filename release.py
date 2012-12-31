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
import urllib2
import getpass
import collections

try:
	import keyring
except Exception:
	pass

VERSION = '0.6.35'

def get_next_version():
	digits = map(int, VERSION.split('.'))
	digits[-1] += 1
	return '.'.join(map(str, digits))

NEXT_VERSION = get_next_version()

files_with_versions = ('docs/conf.py', 'setup.py', 'release.py',
	'README.txt', 'distribute_setup.py')

def get_repo_name():
	"""
	Get the repo name from the hgrc default path.
	"""
	default = subprocess.check_output('hg paths default').strip()
	parts = default.split('/')
	if parts[-1] == '':
		parts.pop()
	return '/'.join(parts[-2:])

def get_mercurial_creds(system='https://bitbucket.org', username=None):
	"""
	Return named tuple of username,password in much the same way that
	Mercurial would (from the keyring).
	"""
	# todo: consider getting this from .hgrc
	username = username or getpass.getuser()
	keyring_username = '@@'.join((username, system))
	system = '@'.join((keyring_username, 'Mercurial'))
	password = (
		keyring.get_password(system, keyring_username)
		if 'keyring' in globals()
		else None
	)
	if not password:
		password = getpass.getpass()
	Credential = collections.namedtuple('Credential', 'username password')
	return Credential(username, password)

def add_milestone_and_version(version=NEXT_VERSION):
	auth = 'Basic ' + ':'.join(get_mercurial_creds()).encode('base64').strip()
	headers = {
		'Authorization': auth,
		}
	base = 'https://api.bitbucket.org'
	for type in 'milestones', 'versions':
		url = (base + '/1.0/repositories/{repo}/issues/{type}'
			.format(repo = get_repo_name(), type=type))
		req = urllib2.Request(url = url, headers = headers,
			data='name='+version)
		try:
			urllib2.urlopen(req)
		except urllib2.HTTPError as e:
			print(e.fp.read())

def bump_versions():
	list(map(bump_version, files_with_versions))

def bump_version(filename):
	with open(filename, 'rb') as f:
		lines = [line.replace(VERSION, NEXT_VERSION) for line in f]
	with open(filename, 'wb') as f:
		f.writelines(lines)

def do_release():
	assert all(map(os.path.exists, files_with_versions)), (
		"Expected file(s) missing")

	assert has_sphinx(), "You must have Sphinx installed to release"

	res = raw_input('Have you read through the SCM changelog and '
		'confirmed the changelog is current for releasing {VERSION}? '
		.format(**globals()))
	if not res.lower().startswith('y'):
		print("Please do that")
		raise SystemExit(1)

	print("Travis-CI tests: http://travis-ci.org/#!/jaraco/distribute")
	res = raw_input('Have you or has someone verified that the tests '
		'pass on this revision? ')
	if not res.lower().startswith('y'):
		print("Please do that")
		raise SystemExit(2)

	subprocess.check_call(['hg', 'tag', VERSION])

	subprocess.check_call(['hg', 'update', VERSION])

	has_docs = build_docs()
	if os.path.isdir('./dist'):
		shutil.rmtree('./dist')
	cmd = [sys.executable, 'setup.py', '-q', 'egg_info', '-RD', '-b', '',
		'sdist', 'register', 'upload']
	if has_docs:
		cmd.append('upload_docs')
	subprocess.check_call(cmd)
	upload_bootstrap_script()

	# update to the tip for the next operation
	subprocess.check_call(['hg', 'update'])

	# we just tagged the current version, bump for the next release.
	bump_versions()
	subprocess.check_call(['hg', 'ci', '-m',
		'Bumped to {NEXT_VERSION} in preparation for next '
		'release.'.format(**globals())])

	# push the changes
	subprocess.check_call(['hg', 'push'])

	add_milestone_and_version()

def has_sphinx():
	try:
		devnull = open(os.path.devnull, 'wb')
		subprocess.Popen(['sphinx-build', '--version'], stdout=devnull,
			stderr=subprocess.STDOUT).wait()
	except Exception:
		return False
	return True

def build_docs():
	if not os.path.isdir('docs'):
		return
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
	return True

def upload_bootstrap_script():
	scp_command = 'pscp' if sys.platform.startswith('win') else 'scp'
	try:
		subprocess.check_call([scp_command, 'distribute_setup.py',
			'pypi@ziade.org:python-distribute.org/'])
	except:
		print("Unable to upload bootstrap script. Ask Tarek to do it.")

if __name__ == '__main__':
	do_release()
