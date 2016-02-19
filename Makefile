empty:
	exit 1

update-vendored:
	rm -rf pkg_resources/_vendor/packaging*
	rm -rf pkg_resources/_vendor/six*
	rm -rf pkg_resources/_vendor/pyparsing*
	python3 -m pip install -r pkg_resources/_vendor/vendored.txt -t pkg_resources/_vendor/
	sed -i 's/ \(pyparsing\|six\)/ pkg_resources.extern.\1/' \
		pkg_resources/_vendor/packaging/*.py
	rm -rf pkg_resources/_vendor/*.{egg,dist}-info
