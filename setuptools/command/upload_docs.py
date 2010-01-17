# -*- coding: utf-8 -*-
"""upload_docs

Implements a Distutils 'upload_docs' subcommand (upload documentation to
PyPI's packages.python.org).
"""

import os
import socket
import zipfile
import httplib
import base64
import urlparse
import tempfile
import cStringIO as StringIO

from distutils import log
from distutils.errors import DistutilsOptionError
from distutils.command.upload import upload

class upload_docs(upload):

    description = 'Upload documentation to PyPI'

    user_options = [
        ('repository=', 'r',
         "url of repository [default: %s]" % upload.DEFAULT_REPOSITORY),
        ('show-response', None,
         'display full response text from server'),
        ('upload-dir=', None, 'directory to upload'),
        ]
    boolean_options = upload.boolean_options

    def initialize_options(self):
        upload.initialize_options(self)
        self.upload_dir = None

    def finalize_options(self):
        upload.finalize_options(self)
        if self.upload_dir is None:
            build = self.get_finalized_command('build')
            self.upload_dir = os.path.join(build.build_base, 'docs')
            self.mkpath(self.upload_dir)
        self.ensure_dirname('upload_dir')
        self.announce('Using upload directory %s' % self.upload_dir)

    def create_zipfile(self):
        name = self.distribution.metadata.get_name()
        tmp_dir = tempfile.mkdtemp()
        tmp_file = os.path.join(tmp_dir, "%s.zip" % name)
        zip_file = zipfile.ZipFile(tmp_file, "w")
        for root, dirs, files in os.walk(self.upload_dir):
            if root == self.upload_dir and not files:
                raise DistutilsOptionError(
                    "no files found in upload directory '%s'"
                    % self.upload_dir)
            for name in files:
                full = os.path.join(root, name)
                relative = root[len(self.upload_dir):].lstrip(os.path.sep)
                dest = os.path.join(relative, name)
                zip_file.write(full, dest)
        zip_file.close()
        return tmp_file

    def run(self):
        zip_file = self.create_zipfile()
        self.upload_file(zip_file)

    def upload_file(self, filename):
        content = open(filename, 'rb').read()
        meta = self.distribution.metadata
        data = {
            ':action': 'doc_upload',
            'name': meta.get_name(),
            'content': (os.path.basename(filename), content),
        }
        # set up the authentication
        credentials = self.username + ':' + self.password
        try:  # base64 only works with bytes in Python 3.
            encoded_creds = base64.encodebytes(credentials.encode('utf8'))
            auth = b"Basic "
        except AttributeError:
            encoded_creds = base64.encodestring(credentials)
            auth = "Basic "
        auth += encoded_creds.strip()

        # Build up the MIME payload for the POST data
        boundary = '--------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
        sep_boundary = '\n--' + boundary
        end_boundary = sep_boundary + '--'
        body = StringIO.StringIO()
        for key, values in data.items():
            # handle multiple entries for the same name
            if type(values) != type([]):
                values = [values]
            for value in values:
                if type(value) is tuple:
                    fn = ';filename="%s"' % value[0]
                    value = value[1]
                else:
                    fn = ""
                value = str(value)
                body.write(sep_boundary)
                body.write('\nContent-Disposition: form-data; name="%s"'%key)
                body.write(fn)
                body.write("\n\n")
                body.write(value)
                if value and value[-1] == '\r':
                    body.write('\n')  # write an extra newline (lurve Macs)
        body.write(end_boundary)
        body.write("\n")
        body = body.getvalue()

        self.announce("Submitting documentation to %s" % (self.repository),
                      log.INFO)

        # build the Request
        # We can't use urllib2 since we need to send the Basic
        # auth right with the first request
        schema, netloc, url, params, query, fragments = \
            urlparse.urlparse(self.repository)
        assert not params and not query and not fragments
        if schema == 'http':
            conn = httplib.HTTPConnection(netloc)
        elif schema == 'https':
            conn = httplib.HTTPSConnection(netloc)
        else:
            raise AssertionError("unsupported schema "+schema)

        data = ''
        loglevel = log.INFO
        try:
            conn.connect()
            conn.putrequest("POST", url)
            conn.putheader('Content-type',
                           'multipart/form-data; boundary=%s'%boundary)
            conn.putheader('Content-length', str(len(body)))
            conn.putheader('Authorization', auth)
            conn.endheaders()
            conn.send(body)
        except socket.error, e:
            self.announce(str(e), log.ERROR)
            return

        r = conn.getresponse()
        if r.status == 200:
            self.announce('Server response (%s): %s' % (r.status, r.reason),
                          log.INFO)
        elif r.status == 301:
            location = r.getheader('Location')
            if location is None:
                location = 'http://packages.python.org/%s/' % meta.get_name()
            self.announce('Upload successful. Visit %s' % location,
                          log.INFO)
        else:
            self.announce('Upload failed (%s): %s' % (r.status, r.reason),
                          log.ERROR)
        if self.show_response:
            print '-'*75, r.read(), '-'*75
