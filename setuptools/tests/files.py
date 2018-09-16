import os


import pkg_resources.py31compat


def build_files(file_defs, prefix=""):
    """
    Build a set of files/directories, as described by the file_defs dictionary.

    Each key/value pair in the dictionary is interpreted as a filename/contents
    pair. If the contents value is a dictionary, a directory is created, and the
    dictionary interpreted as the files within it, recursively.

    For example:

    {"README.txt": "A README file",
     "foo": {
        "__init__.py": "",
        "bar": {
            "__init__.py": "",
        },
        "baz.py": "# Some code",
     }
    }
    """
    for name, contents in file_defs.items():
        full_name = os.path.join(prefix, name)
        if isinstance(contents, dict):
            pkg_resources.py31compat.makedirs(full_name, exist_ok=True)
            build_files(contents, prefix=full_name)
        else:
            if isinstance(contents, bytes):
                with open(full_name, 'wb') as f:
                    f.write(contents)
            else:
                with open(full_name, 'w') as f:
                    f.write(contents)
