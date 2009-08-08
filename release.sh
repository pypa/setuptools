#!/bin/sh

export VERSION="0.6"

# creating the releases
rm -rf dist

# eggs
python2.3 setup.py -q egg_info -RDb '' bdist_egg # manual upload
python2.4 setup.py -q egg_info -RDb '' bdist_egg # manual upload
python2.5 setup.py -q egg_info -RDb '' bdist_egg register upload
python2.6 setup.py -q egg_info -RDb '' bdist_egg register upload

# updating the md5 hashes
python distribute_setup.py --md5update dist/distribute-$VERSION-py2.3.egg
python distribute_setup.py --md5update dist/distribute-$VERSION-py2.4.egg
python distribute_setup.py --md5update dist/distribute-$VERSION-py2.5.egg
python distribute_setup.py --md5update dist/distribute-$VERSION-py2.6.egg

# now preparing the source release
python2.6 setup.py -q egg_info -RDb '' sdist register upload

echo You need to commit the md5 changes


