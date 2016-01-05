empty:
	exit 1

update-vendored:
	rm -rf pkg_resources/_vendor/packaging*
	rm -rf pkg_resources/_vendor/six*
	python3 -m pip install -r pkg_resources/_vendor/vendored.txt -t pkg_resources/_vendor/
	rm -rf pkg_resources/_vendor/*.{egg,dist}-info
