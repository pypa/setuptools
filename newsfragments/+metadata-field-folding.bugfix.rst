Continuation lines are now folded when writing ``PKG-INFO``/``METADATA``, so a
newline embedded in a metadata value (for example ``project.authors``) can no
longer introduce an extra core metadata field such as ``Requires-Dist``.
