empty:
	exit 1

update-vendored:
	rm -rf pkg_resources/_vendor/packaging
	rm -rf pkg_resources/_vendor/pyparsing
	pip install -r pkg_resources/_vendor/vendored.txt -t pkg_resources/_vendor/
	sed -i -e 's/ \(pyparsing\)/ pkg_resources._vendor.\1/' \
		pkg_resources/_vendor/packaging/*.py
	rm -rf pkg_resources/_vendor/*.{egg,dist}-info
