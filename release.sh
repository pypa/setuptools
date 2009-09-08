#!/bin/sh
export VERSION="0.6.2"

# creating the releases
rm -rf dist

# now preparing the source release
python2.6 setup.py -q egg_info -RDb '' sdist register upload

# pushin the bootstrap script
scp distribute_setup.py ziade.org:nightly/build/

