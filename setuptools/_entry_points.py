import functools
import operator

from pkg_resources import yield_lines
from ._importlib import metadata
from ._itertools import ensure_unique


@functools.singledispatch
def render_items(value):
    """
    Given a value of an entry point or series of entry points,
    return each entry point on a single line.
    """
    # normalize to a single sequence of lines
    lines = yield_lines(value)
    parsed = metadata.EntryPoints._from_text('[x]\n' + '\n'.join(lines))
    valid = ensure_unique(parsed, key=operator.attrgetter('name'))

    def ep_to_str(ep):
        return f'{ep.name} = {ep.value}'
    return '\n'.join(sorted(map(ep_to_str, valid)))


render_items.register(str, lambda x: x)


@functools.singledispatch
def render(eps):
    """
    Given a Distribution.entry_points, produce a multiline
    string definition of those entry points.
    """
    return ''.join(
        f'[{section}]\n{render_items(contents)}\n\n'
        for section, contents in sorted(eps.items())
    )


render.register(type(None), lambda x: x)
render.register(str, lambda x: x)
