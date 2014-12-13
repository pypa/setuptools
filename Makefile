empty:
	exit 1

update-vendored:
	rm -rf setuptools/_vendor/packaging
	pip install -r setuptools/_vendor/vendored.txt -t setuptools/_vendor/
	rm -rf setuptools/_vendor/*.{egg,dist}-info
