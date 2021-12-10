import json
import difflib


def diff(obj1, obj2, label1="left", label2="right") -> str:
    """Attempt to create a string representation of the difference between 2
    objects. If the objects contain a weird data type that cannot be serialised to
    JSON, this function will simply convert it to str.
    """

    left = json.dumps(_make_comparable(obj1), indent=2, sort_keys=True)
    right = json.dumps(_make_comparable(obj2), indent=2, sort_keys=True)
    delta = difflib.unified_diff(
        left.splitlines(True),
        right.splitlines(True),
        fromfile=label1,
        tofile=label2
    )
    return "".join(delta)


def _make_comparable(obj):
    # It is not easy to force JSONEconder to sort arrays, so we pre-process
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    if isinstance(obj, (list, tuple)):
        comparable = [_make_comparable(x) for x in obj]
        try:
            return sorted(comparable)
        except Exception:
            return comparable

    if isinstance(obj, dict):
        return {k: _make_comparable(v) for k, v in obj.items()}

    return str(obj)
