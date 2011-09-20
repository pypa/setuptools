from distutils.command.register import register as _register
from ConfigParser import ConfigParser
import os

class register(_register):
    __doc__ = _register.__doc__

    def run(self):
        # Make sure that we are using valid current name/version info
        self.run_command('egg_info')
        self._section_name = self.repository
        _register.run(self)

    def _read_pypirc(self):
        """Reads the .pypirc file."""
        rc = self._get_rc_file()
        if os.path.exists(rc):
            repository = self.repository
            config = ConfigParser()
            config.read(rc)
            sections = config.sections()
            if 'distutils' in sections:
                # let's get the list of servers
                index_servers = config.get('distutils', 'index-servers')
                _servers = [server.strip() for server in
                            index_servers.split('\n')
                            if server.strip() != '']
                if _servers == []:
                    # nothing set, let's try to get the default pypi
                    if 'pypi' in sections:
                        _servers = ['pypi']
                    else:
                        # the file is not properly defined, returning
                        # an empty dict
                        return {}
                for server in _servers:
                    current = {'server': server}
                    current['username'] = config.get(server, 'username')

                    # optional params
                    for key, default in (('repository',
                                          None),
                                         ('realm', self.DEFAULT_REALM),
                                         ('password', None)):
                        if config.has_option(server, key):
                            current[key] = config.get(server, key)
                        else:
                            current[key] = default
                    if (current['server'] == repository or
                        current['repository'] == repository):
                        return current
            elif 'server-login' in sections:
                # old format
                server = 'server-login'
                if config.has_option(server, 'repository'):
                    repository = config.get(server, 'repository')
                else:
                    repository = None
                return {'username': config.get(server, 'username'),
                        'password': config.get(server, 'password'),
                        'repository': repository,
                        'server': server,
                        'realm': self.DEFAULT_REALM}

        return {}

    def _set_config(self):
        _register._set_config(self)
        if self.repository is None:
                raise ValueError('%s is missing a repository value in .pypirc' % self._section_name)
