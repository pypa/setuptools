"""Basic http server for tests to simulate PyPI or custom indexes
"""
import urllib2
import sys
from threading import Thread
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

class IndexServer(HTTPServer):
    """Basic single-threaded http server simulating a package index

    You can use this server in unittest like this::
        s = IndexServer()
        s.start()
        index_url = s.base_url() + 'mytestindex'
        # do some test requests to the index
        # The index files should be located in setuptools/tests/indexes
        s.stop()
    """
    def __init__(self):
        HTTPServer.__init__(self, ('', 0), SimpleHTTPRequestHandler)
        self._run = True

    def serve(self):
        while True:
            self.handle_request()
            if not self._run: break

    def start(self):
        self.thread = Thread(target=self.serve)
        self.thread.start()

    def stop(self):
        """self.shutdown is not supported on python < 2.6"""
        self._run = False
        try:
            if sys.version > '2.6':
                urllib2.urlopen('http://127.0.0.1:%s/' % self.server_port,
                                None, 5)
            else:
                urllib2.urlopen('http://127.0.0.1:%s/' % self.server_port)
        except urllib2.URLError:
            pass
        self.thread.join()

    def base_url(self):
        port = self.server_port
        return 'http://127.0.0.1:%s/setuptools/tests/indexes/' % port
