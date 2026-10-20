``setuptools.archive_util`` no longer applies the setuid, setgid or sticky
bits recorded in a zip archive to the files it extracts, which includes
wheels unpacked by ``Wheel.install_as_egg``. The read, write and execute
permission bits are still honored.
