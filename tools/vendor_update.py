#!/bin/env python3

import contextlib
import subprocess
import re
import requests
import shutil
import tarfile
import tempfile

from pathlib import Path


def run(*args):
    return subprocess.check_output(args).decode()


def get_vendors_diff(file_path):
    return run("git", "diff", "--no-color", "--", file_path)


def parse_vendors_diff(diff):
    r = re.compile(r'^(-|\+)(.*?)==(.*?)$', re.M)
    ret = {}
    for m in r.finditer(diff):
        tp, name, ver = m.groups()
        if tp == '-':
            ret.setdefault(name, {})['old'] = ver
        else:
            assert tp == '+'
            ret.setdefault(name, {})['new'] = ver
    return ret


def get_sdist(name, ver, chunk_size=128*1024):
    url = f"https://pypi.io/packages/source/{name[0]}/{name}/{name}-{ver}.tar.gz"
    print(f"Downloading sdist from {url}")
    tmpdir = tempfile.TemporaryDirectory()
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with tempfile.TemporaryFile("w+b") as tmpf:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    tmpf.write(chunk)
                tmpf.seek(0)
                with tarfile.open(fileobj=tmpf, mode="r:gz") as tar:
                    tar.extractall(tmpdir.name)
    except:
        tmpdir.cleanup()
        raise
    return tmpdir


def find_package_path(pkg_root_path, pkg_name):
    pkg_root_path = next(pkg_root_path.iterdir())
    singlefiles = (
        pkg_root_path / f"{pkg_name}.py",
        pkg_root_path / "src" / f"{pkg_name}.py"
    )
    dirs = (
            pkg_root_path / pkg_name,
            pkg_root_path / "src" / pkg_name,
    )
    for p in singlefiles:
        if p.is_file():
            return p
    for p in dirs:
        if p.is_dir() and (p / "__init__.py").is_file():
            return p
    raise NotImplementedError("Package path is not found")


def create_patch(vendor_path):
    print("Creating patch")
    f = tempfile.NamedTemporaryFile("w+")
    try:
        diff = run("git", "diff", "-R", "--", str(vendor_path))
        f.write(diff)
        f.flush()
        return f
    except:
        f.close()
        raise


def apply_patch(patch):
    print("Applying patch")
    if patch.stat().st_size != 0:
        run("git", "apply", str(patch))
    else:
        print("Skipping due to empty patch")


def move_path(src, dst):
    shutil.move(str(src), str(dst))


def remove_path(p):
    if p.is_dir():
        shutil.rmtree(str(p))
    else:
        p.unlink()


def handle_update(root_path, pkg_name, old_ver, new_ver):
    print(f"# Updating package '{pkg_name}' from version v{old_ver} to v{new_ver}")

    with contextlib.ExitStack() as ctx:
        vendor_path = root_path / pkg_name
        if not vendor_path.is_dir() or not (vendor_path / "__init__.py").is_file():
            vendor_path = root_path / f"{pkg_name}.py"
            assert vendor_path.is_file()

        print(f"Vendor path is {vendor_path}")

        old_path = Path(ctx.enter_context(get_sdist(pkg_name, old_ver)))
        new_path = Path(ctx.enter_context(get_sdist(pkg_name, new_ver)))

        print("Creating backup")
        vendor_path_backup = root_path / (pkg_name + ".tmp")
        move_path(vendor_path, vendor_path_backup)
        try:
            print(f"Copying original files from v{old_ver}")
            old_pkg_path = find_package_path(old_path, pkg_name)
            move_path(old_pkg_path, vendor_path)
            patch = Path(ctx.enter_context(create_patch(vendor_path)).name)
            remove_path(vendor_path)

            print(f"Copying original files from v{new_ver}")
            new_pkg_path = find_package_path(new_path, pkg_name)
            move_path(new_pkg_path, vendor_path)
            apply_patch(patch)
        except:
            print(f"Rolling back '{pkg_name}' due to an error")
            remove_path(vendor_path)
            move_path(vendor_path_backup, vendor_path)
            raise

        print("Removing backup")
        remove_path(vendor_path_backup)

        print("Done")


def update_vendors(root_path, file_path):
    diff = get_vendors_diff(file_path)
    changes = parse_vendors_diff(diff)
    for pkg_name, d in changes.items():
        handle_update(root_path, pkg_name, d['old'], d['new'])


if __name__ == "__main__":
    repo_root = run("git", "rev-parse", "--show-toplevel").strip()
    repo_root = Path(repo_root)
    if not repo_root.is_dir():
        raise ValueError("Invalid repository root %s" % str(repo_root))
    for p in ("pkg_resources", "setuptools"):
        print(f"# Checking vendors of {p}")
        p = repo_root / p / "_vendor"
        update_vendors(p, p / "vendored.txt")
    print("# Done")
