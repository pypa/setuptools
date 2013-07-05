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
import itertools
import re

try:
	import keyring
except Exception:
	pass

VERSION = '0.7.9'
PACKAGE_INDEX = 'https://pypi.python.org/pypi'

def set_versions():
	global VERSION
	version = raw_input("Release as version [%s]> " % VERSION) or VERSION
	if version != VERSION:
		VERSION = bump_versions(version)

def infer_next_version(version):
	"""
	Infer a next version from the current version by incrementing the last
	number or appending a number.

	>>> infer_next_version('1.0')
	'1.1'

	>>> infer_next_version('1.0b')
	'1.0b1'

	>>> infer_next_version('1.0.9')
	'1.0.10'

	>>> infer_next_version('1')
	'2'

	>>> infer_next_version('')
	'1'
	"""
	def incr(match):
		ver = int(match.group(0) or '0')
		return str(ver + 1)
	return re.sub('\d*$', incr, version)

files_with_versions = (
	'docs/conf.py', 'setup.py', 'release.py', 'ez_setup.py', 'README.txt',
	'setuptools/__init__.py',
)

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
	system = 'Mercurial'
	password = (
		keyring.get_password(system, keyring_username)
		if 'keyring' in globals()
		else None
	)
	if not password:
		password = getpass.getpass()
	Credential = collections.namedtuple('Credential', 'username password')
	return Credential(username, password)

def add_milestone_and_version(version):
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

def bump_versions(target_ver):
	for filename in files_with_versions:
		bump_version(filename, target_ver)
	subprocess.check_call(['hg', 'ci', '-m',
		'Bumped to {target_ver} in preparation for next '
		'release.'.format(**vars())])
	return target_ver

def bump_version(filename, target_ver):
	with open(filename, 'rb') as f:
		lines = [line.replace(VERSION, target_ver) for line in f]
	with open(filename, 'wb') as f:
		f.writelines(lines)

def do_release():
	assert all(map(os.path.exists, files_with_versions)), (
		"Expected file(s) missing")

	assert has_sphinx(), "You must have Sphinx installed to release"

	set_versions()

	res = raw_input('Have you read through the SCM changelog and '
		'confirmed the changelog is current for releasing {VERSION}? '
		.format(**globals()))
	if not res.lower().startswith('y'):
		print("Please do that")
		raise SystemExit(1)

	print("Travis-CI tests: http://travis-ci.org/#!/jaraco/setuptools")
	res = raw_input('Have you or has someone verified that the tests '
		'pass on this revision? ')
	if not res.lower().startswith('y'):
		print("Please do that")
		raise SystemExit(2)

	subprocess.check_call(['hg', 'tag', VERSION])

	subprocess.check_call(['hg', 'update', VERSION])

	upload_to_pypi()

	# update to the tip for the next operation
	subprocess.check_call(['hg', 'update'])

	# we just tagged the current version, bump for the next release.
	next_ver = bump_versions(infer_next_version(VERSION))

	# push the changes
	subprocess.check_call(['hg', 'push'])

	add_milestone_and_version(next_ver)

def upload_to_pypi():
	linkify('CHANGES.txt', 'CHANGES (links).txt')

	has_docs = build_docs()
	if os.path.isdir('./dist'):
		shutil.rmtree('./dist')
	cmd = [
		sys.executable, 'setup.py', '-q',
		'egg_info', '-RD', '-b', '',
		'sdist',
		#'register', '-r', PACKAGE_INDEX,
		#'upload', '-r', PACKAGE_INDEX,
	]
	if has_docs:
		cmd.extend([
			'upload_docs', '-r', PACKAGE_INDEX
		])
	subprocess.check_call(cmd)

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
	cmd = [
		'sphinx-build',
		'-b', 'html',
		'-d', 'build/doctrees',
		'.',
		'build/html',
	]
	subprocess.check_call(cmd, cwd='docs')
	return True

def linkify(source, dest):
	with open(source) as source:
		out = _linkified_text(source.read())
	with open(dest, 'w') as dest:
		dest.write(out)

def _linkified(rst_path):
	"return contents of reStructureText file with linked issue references"
	rst_file = open(rst_path)
	rst_content = rst_file.read()
	rst_file.close()

	return _linkified_text(rst_content)

def _linkified_text(rst_content):
	# first identify any existing HREFs so they're not changed
	HREF_pattern = re.compile('`.*?`_', re.MULTILINE | re.DOTALL)

	# split on the HREF pattern, returning the parts to be linkified
	plain_text_parts = HREF_pattern.split(rst_content)
	anchors = []
	linkified_parts = [_linkified_part(part, anchors)
		for part in plain_text_parts]
	pairs = itertools.izip_longest(
		linkified_parts,
		HREF_pattern.findall(rst_content),
		fillvalue='',
	)
	rst_content = ''.join(flatten(pairs))

	anchors = sorted(anchors)

	bitroot = 'https://bitbucket.org/tarek/distribute'
	rst_content += "\n"
	for x in anchors:
		issue = re.findall(r'\d+', x)[0]
		rst_content += '.. _`%s`: %s/issue/%s\n' % (x, bitroot, issue)
	rst_content += "\n"
	return rst_content

def flatten(listOfLists):
	"Flatten one level of nesting"
	return itertools.chain.from_iterable(listOfLists)


def _linkified_part(text, anchors):
	"""
	Linkify a part and collect any anchors generated
	"""
	revision = re.compile(r'\b(issue\s+#?\d+)\b', re.M | re.I)

	anchors.extend(revision.findall(text)) # ['Issue #43', ...]
	return revision.sub(r'`\1`_', text)

if __name__ == '__main__':
	do_release()
