#!/bin/sh
export VERSION="0.6.4"

# creating the 3k script
cp distribute_setup.py distribute_setup.py.back 
2to3 -w distribute_setup.py > /dev/null 
mv distribute_setup.py distribute_setup_3k.py 
mv distribute_setup.py.back distribute_setup.py

# creating the releases
rm -rf dist

# now preparing the source release
python2.6 setup.py -q egg_info -RDb '' sdist register upload

# pushing the bootstrap script
scp distribute_setup.py ziade.org:nightly/build/

