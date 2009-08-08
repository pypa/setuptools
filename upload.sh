# upload for 2.5 and 2.6
# 2.3 and 2.4 are manual
python2.5 setup.py egg_info -RDb '' bdist_egg register upload
python2.6 setup.py egg_info -RDb '' bdist_egg sdist register upload


