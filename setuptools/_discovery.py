import functools
import operator

import packaging.requirements


# from coherent.build.discovery
def extras_from_markers(markers):
    """Collect the names defined by ``extra == ...`` markers.

    ``Marker._markers`` nests parenthesised sub-expressions as lists, so the
    tree must be walked recursively. Only equality markers define an extra;
    ``extra != ...`` is deliberately ignored.
    """
    extras = set()
    for marker in markers:
        if isinstance(marker, list):
            extras.update(extras_from_markers(marker))
        elif (
            isinstance(marker, tuple)
            and marker[0].value == 'extra'
            and marker[1].value == '=='
        ):
            extras.add(marker[2].value)
    return extras


def extras_from_dep(dep):
    try:
        markers = packaging.requirements.Requirement(dep).marker._markers
    except AttributeError:
        markers = ()
    return extras_from_markers(markers)


def extras_from_deps(deps):
    """
    >>> extras_from_deps(['requests'])
    set()
    >>> extras_from_deps(['pytest; extra == "test"'])
    {'test'}
    >>> sorted(extras_from_deps([
    ...     'requests',
    ...     'pytest; extra == "test"',
    ...     'pytest-cov; extra == "test"',
    ...     'sphinx; extra=="doc"']))
    ['doc', 'test']
    >>> extras_from_deps(['x; (extra == "test") and (python_version > "3")'])
    {'test'}
    >>> extras_from_deps(['x; extra != "test"'])
    set()
    """
    return functools.reduce(operator.or_, map(extras_from_dep, deps), set())
