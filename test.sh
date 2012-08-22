#!/bin/sh
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

echo -n "Running tests for Python 2.7..."
python2.7 setup.py -q test > /dev/null 2> /dev/null
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

rm -rf build
echo -n "Running tests for Python 3.2..."
python3.2 setup.py -q test > /dev/null 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit $1
else
    echo "Success"
fi

rm -rf build
echo -n "Running tests for Python 3.3..."
python3.3 setup.py -q test > /dev/null 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit $1
else
    echo "Success"
fi

