#!/bin/sh

export VERSION="0.6"

# creating the releases
rm -rf dist

# eggs
python2.3 setup.py -q egg_info -RDb '' bdist_egg
python2.4 setup.py -q egg_info -RDb '' bdist_egg
python2.5 setup.py -q egg_info -RDb '' bdist_egg
python2.6 setup.py -q egg_info -RDb '' bdist_egg

# source
python2.6 setup.py -q egg_info -RDb '' sdist

# updating the md5 hashes
python ez_setup.py --md5update dist/distribute-$VERSION-py2.3.egg
python ez_setup.py --md5update dist/distribute-$VERSION-py2.4.egg
python ez_setup.py --md5update dist/distribute-$VERSION-py2.5.egg
python ez_setup.py --md5update dist/distribute-$VERSION-py2.6.egg

# XXX uploads will be done here

