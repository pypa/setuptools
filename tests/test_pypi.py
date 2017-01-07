import os
import subprocess

import virtualenv
from setuptools.extern.six.moves import http_client
from setuptools.extern.six.moves import xmlrpc_client

TOP = 200
PYPI_HOSTNAME = 'pypi.python.org'


def rpc_pypi(method, *args):
    """Call an XML-RPC method on the Pypi server."""
    conn = http_client.HTTPSConnection(PYPI_HOSTNAME)
    headers = {'Content-Type': 'text/xml'}
    payload = xmlrpc_client.dumps(args, method)

    conn.request("POST", "/pypi", payload, headers)
    response = conn.getresponse()
    if response.status == 200:
        result = xmlrpc_client.loads(response.read())[0][0]
        return result
    else:
        raise RuntimeError("Unable to download the list of top "
                           "packages from Pypi.")


def get_top_packages(limit):
    """Collect the name of the top packages on Pypi."""
    packages = rpc_pypi('top_packages')
    return packages[:limit]


def _package_install(package_name, tmp_dir=None, local_setuptools=True):
    """Try to install a package and return the exit status.

    This function creates a virtual environment, install setuptools using pip
    and then install the required package. If local_setuptools is True, it
    will install the local version of setuptools.
    """
    package_dir = os.path.join(tmp_dir, "test_%s" % package_name)
    if not local_setuptools:
        package_dir = package_dir + "_baseline"

    virtualenv.create_environment(package_dir)

    pip_path = os.path.join(package_dir, "bin", "pip")
    if local_setuptools:
        subprocess.check_call([pip_path, "install", "."])
    returncode = subprocess.call([pip_path, "install", package_name])
    return returncode


def test_package_install(package_name, tmpdir):
    """Test to verify the outcome of installing a package.

    This test compare that the return code when installing a package is the
    same as with the current stable version of setuptools.
    """
    new_exit_status = _package_install(package_name, tmp_dir=str(tmpdir))
    if new_exit_status:
        print("Installation failed, testing against stable setuptools",
              package_name)
        old_exit_status = _package_install(package_name, tmp_dir=str(tmpdir),
                                           local_setuptools=False)
        assert new_exit_status == old_exit_status


def pytest_generate_tests(metafunc):
    """Generator function for test_package_install.

    This function will generate calls to test_package_install. If a package
    list has been specified on the command line, it will be used. Otherwise,
    Pypi will be queried to get the current list of top packages.
    """
    if "package_name" in metafunc.fixturenames:
        if not metafunc.config.option.package_name:
            packages = get_top_packages(TOP)
            packages = [name for name, downloads in packages]
        else:
            packages = metafunc.config.option.package_name
        metafunc.parametrize("package_name", packages)
