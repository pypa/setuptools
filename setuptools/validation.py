"""
Validation logic for package metadata, supporting PEP 566.
See: https://www.python.org/dev/peps/pep-0566/
"""


def single_line_str(val):
    """A string that does not contain newline characters"""
    if val is None:
        return
    assert isinstance(val, str), \
        "is of type %s but should be of type str" % type(val)
    assert '\n' not in val, \
        "to contain a newline character (not allowed)"


def multi_line_str(val):
    """A string that can contain newline characters"""
    if val is None:
        return
    assert isinstance(val, str), \
        "is of type %s but should be of type str" % type(val)


def list_of_str(val):
    """A list of single-line text strings"""
    if val is None:
        return
    assert isinstance(val, list), \
        "is of type %s but should be of type list(str)" % type(val)
    for item in val:
        single_line_str(item)


def set_of_str(val):
    """A set (i.e. a list of unique entries) of single-line text strings"""
    if val is None:
        return
    assert isinstance(val, set), \
        "is of type %s but should be of type set(str)" % type(val)
    for item in val:
        single_line_str(item)


default_validator = single_line_str
validators = dict(
    long_description=multi_line_str,
    classifiers=list_of_str,
    keywords=list_of_str,
    platforms=list_of_str,
    project_urls=list_of_str,
    requires=list_of_str,
    provides=list_of_str,
    provides_extras=set_of_str,
    obsoletes=list_of_str,
)


class Metadata:
    """
    A validation object for PKG-INFO data fields
    """

    def __init__(self, *data_dicts, **kwargs):
        """
        Takes JSON-compatible metadata, as described in PEP 566, which
        can be added as both dictionaries or keyword arguments.
        """
        self.errors = []
        self.fields = []

        for data in data_dicts:
            for key in data:
                setattr(self, key, data[key])
                self.fields += [key]

        for key in kwargs:
            setattr(self, key, kwargs[key])
            self.fields += [key]

    def validate(self, throw_exception=False):
        """
        Runs validation over all data, and sets the ``error`` attribute
        in case of validation errors.
        """
        self.errors = []

        for field in self.fields:
            validator = validators.get(field, default_validator)
            val = getattr(self, field)
            try:
                validator(val)
            except AssertionError as err:
                self.errors += [(field, err)]

        if throw_exception and self.errors:
            raise InvalidMetadataError(self.errors)

        return not self.errors


class InvalidMetadataError(ValueError):
    """An error that can be raised when validation fails"""

    def __init__(self, error_list):
        self.errors = error_list
