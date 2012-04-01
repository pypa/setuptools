"""Basic http server for tests to simulate PyPI or custom indexes
"""
import urllib2
import sys
import threading
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
    def __init__(self, server_address=('', 0),
            RequestHandlerClass=SimpleHTTPRequestHandler,
            bind_and_activate=True):
        HTTPServer.__init__(self, server_address, RequestHandlerClass,
            bind_and_activate)
        self._run = True

    def serve(self):
        while self._run:
            self.handle_request()

    def start(self):
        self.thread = threading.Thread(target=self.serve)
        self.thread.start()

    def stop(self):
        "Stop the server"

        # self.shutdown is not supported on python < 2.6, so just
        #  set _run to false, and make a request, causing it to
        #  terminate.
        self._run = False
        url = 'http://127.0.0.1:%(server_port)s/' % vars(self)
        try:
            if sys.version_info >= (2, 6):
                urllib2.urlopen(url, timeout=5)
            else:
                urllib2.urlopen(url)
        except urllib2.URLError:
            # ignore any errors; all that's important is the request
            pass
        self.thread.join()

    def base_url(self):
        port = self.server_port
        return 'http://127.0.0.1:%s/setuptools/tests/indexes/' % port
