from textwrap import dedent

import pytest

from setuptools.diff_utils import diff


class _Obj:
    def __init__(self, _repr):
        self._repr = _repr

    def __str__(self):
        return str(self._repr)


@pytest.mark.parametrize("example1,example2", [
    ({"a": (1, 2, 3), "b": [-1, 1]}, {"b": [1, -1], "a": [1, 2, 3]}),
    (_Obj(1), _Obj(1))
])
def test_no_diff(example1, example2):
    delta = diff(example1, example2)
    assert len(delta.strip()) == 0


@pytest.mark.parametrize("example1,example2", [
    ({"a": (1, 2, 3), "b": [-1, 1]}, {"b": [1], "c": [1, 2, 3]}),
])
def test_diff(example1, example2):
    delta = diff(example1, example2)
    expected = """\
        --- left
        +++ right
        @@ -1,11 +1,10 @@
         {
        -  "a": [
        +  "b": [
        +    1
        +  ],
        +  "c": [
             1,
             2,
             3
        -  ],
        -  "b": [
        -    -1,
        -    1
           ]
         }
    """
    assert delta.strip() == dedent(expected).strip()
