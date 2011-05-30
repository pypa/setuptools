#!/bin/sh
export VERSION="0.6.17"

# tagging
hg tag $VERSION
hg ci -m "bumped revision"

# creating the releases
rm -rf ./dist

# now preparing the source release, pushing it and its doc
python2.6 setup.py -q egg_info -RDb '' sdist register upload
cd docs/
make html
cd ..
python2.6 setup.py upload_docs

# pushing the bootstrap script
scp distribute_setup.py ziade.org:websites/python-distribute.org/

# starting the new dev
hg push

