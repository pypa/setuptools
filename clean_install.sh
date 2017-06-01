#!/usr/bin/env bash

set -o errexit
set -o xtrace

# Create a temporary directory to install the virtualenv in
VENV_DIR="$(mktemp -d)"
function cleanup() {
  rm -rf "$VENV_DIR"
}
trap cleanup EXIT

# Create a virtualenv that doesn't have pip or setuptools installed
wget https://raw.githubusercontent.com/pypa/virtualenv/master/virtualenv.py
python virtualenv.py --no-wheel --no-pip --no-setuptools "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Now try to install setuptools
python bootstrap.py
python setup.py install
