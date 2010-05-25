#!/bin/sh
echo -n "Running tests for Python 2.3..."
python2.3 setup.py -q test > /dev/null 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit $1
else
    echo "Success"
fi

echo -n "Running tests for Python 2.4..."
python2.4 setup.py -q test > /dev/null 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit $1
else
    echo "Success"
fi

echo -n "Running tests for Python 2.5..."
python2.5 setup.py -q test > /dev/null 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit $1
else
    echo "Success"
fi

echo -n "Running tests for Python 2.6..."
python2.6 setup.py -q test > /dev/null 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit $1
else
    echo "Success"
fi

rm -rf build
echo -n "Running tests for Python 3.1..."
python3.1 setup.py -q test > /dev/null 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit $1
else
    echo "Success"
fi

