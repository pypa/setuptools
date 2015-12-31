empty:
	exit 1

update-vendored:
	rm -rf pkg_resources/_vendor/packaging
	python3.5 -m pip install -r pkg_resources/_vendor/vendored.txt -t pkg_resources/_vendor/
	rm -rf pkg_resources/_vendor/*.{egg,dist}-info

	rm -rf setuptools/_vendor/six
	python3.5 -m pip install -r setuptools/_vendor/vendored.txt -t setuptools/_vendor/
	rm -rf setuptools/_vendor/*.{egg,dist}-info
