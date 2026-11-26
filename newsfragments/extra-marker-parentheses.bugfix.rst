Fixed conversion of wheel metadata into egg metadata when an ``extra ==``
marker was wrapped in parentheses. Such dependencies are now recognised and
assigned to the correct extra instead of being dropped. Markers using
``extra !=`` are no longer mistaken for definitions of an extra.
