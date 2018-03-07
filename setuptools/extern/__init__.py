from .importer import VendorImporter

names = 'pkg_resources', 'six', 'packaging', 'appdirs'
VendorImporter(__name__, names, 'setuptools._vendor').install()
