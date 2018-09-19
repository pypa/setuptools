"""Utils to be used for the setup() package_data argument."""
import os


def get_pkg_data(pkg_name, data_dirs, extensions):
    """Recursively get package data.

    This should be called from within setup.py's setuptools.setup() function,
    e.g. package_data={'my_package': get_pkg_data(pkg_name='my_pckage', ...)}

    Args:
        pkg_name (str): Name of package containing package data.
        data_dirs (list):
        extensions (list):

    Returns:
        list: List of glob strings where each string represents a terminal
        branch node (i.e. folder) and a glob of all files ending in designated
        extension(s).

    Examples:
        Args: get_pkg_data(pkg_name='my_package',
        src_dirs=['templates'], extensions=['html'])

        Returns: [
        'templates/*.html',
        'templates/content/*.html',
        'templates/content/prompt/*.html',
        'templates/content/prompt/inputs/*.html']
    """
    pkg_root = \
        os.path.dirname(os.path.realpath(__file__)) + '/{}/'.format(pkg_name)
    pkg_data = []
    for _dir in data_dirs:
        for ext in extensions:
            for i, j, y in os.walk(pkg_root + _dir):
                pkg_data.append(i + '/*.' + ext)
    return pkg_data
