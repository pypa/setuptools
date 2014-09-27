# Copyright 2014 Donald Stufft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import, division, print_function

import collections
import itertools
import re

from ._compat import string_types
from ._structures import Infinity


__all__ = [
    "parse", "Version", "LegacyVersion", "InvalidVersion", "Specifier",
    "InvalidSpecifier",
]


_Version = collections.namedtuple(
    "_Version",
    ["epoch", "release", "dev", "pre", "post", "local"],
)


def parse(version):
    """
    Parse the given version string and return either a :class:`Version` object
    or a :class:`LegacyVersion` object depending on if the given version is
    a valid PEP 440 version or a legacy version.
    """
    try:
        return Version(version)
    except InvalidVersion:
        return LegacyVersion(version)


class InvalidVersion(ValueError):
    """
    An invalid version was found, users should refer to PEP 440.
    """


class _BaseVersion(object):

    def __hash__(self):
        return hash(self._key)

    def __lt__(self, other):
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)

    def _compare(self, other, method):
        if not isinstance(other, _BaseVersion):
            return NotImplemented

        return method(self._key, other._key)


class LegacyVersion(_BaseVersion):

    def __init__(self, version):
        self._version = str(version)
        self._key = _legacy_cmpkey(self._version)

    def __str__(self):
        return self._version

    def __repr__(self):
        return "<LegacyVersion({0})>".format(repr(str(self)))

    @property
    def public(self):
        return self._version

    @property
    def local(self):
        return None

    @property
    def is_prerelease(self):
        return False


_legacy_version_component_re = re.compile(
    r"(\d+ | [a-z]+ | \.| -)", re.VERBOSE,
)

_legacy_version_replacement_map = {
    "pre": "c", "preview": "c", "-": "final-", "rc": "c", "dev": "@",
}


def _parse_version_parts(s):
    for part in _legacy_version_component_re.split(s):
        part = _legacy_version_replacement_map.get(part, part)

        if not part or part == ".":
            continue

        if part[:1] in "0123456789":
            # pad for numeric comparison
            yield part.zfill(8)
        else:
            yield "*" + part

    # ensure that alpha/beta/candidate are before final
    yield "*final"


def _legacy_cmpkey(version):
    # We hardcode an epoch of -1 here. A PEP 440 version can only have a epoch
    # greater than or equal to 0. This will effectively put the LegacyVersion,
    # which uses the defacto standard originally implemented by setuptools,
    # as before all PEP 440 versions.
    epoch = -1

    # This scheme is taken from pkg_resources.parse_version setuptools prior to
    # it's adoption of the packaging library.
    parts = []
    for part in _parse_version_parts(version.lower()):
        if part.startswith("*"):
            # remove "-" before a prerelease tag
            if part < "*final":
                while parts and parts[-1] == "*final-":
                    parts.pop()

            # remove trailing zeros from each series of numeric parts
            while parts and parts[-1] == "00000000":
                parts.pop()

        parts.append(part)
    parts = tuple(parts)

    return epoch, parts


class Version(_BaseVersion):

    _regex = re.compile(
        r"""
        ^
        \s*
        v?
        (?:
            (?:(?P<epoch>[0-9]+)!)?                           # epoch
            (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
            (?P<pre>                                          # pre-release
                [-_\.]?
                (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
                [-_\.]?
                (?P<pre_n>[0-9]+)?
            )?
            (?P<post>                                         # post release
                (?:-(?P<post_n1>[0-9]+))
                |
                (?:
                    [-_\.]?
                    (?P<post_l>post|rev|r)
                    [-_\.]?
                    (?P<post_n2>[0-9]+)?
                )
            )?
            (?P<dev>                                          # dev release
                [-_\.]?
                (?P<dev_l>dev)
                [-_\.]?
                (?P<dev_n>[0-9]+)?
            )?
        )
        (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
        \s*
        $
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    def __init__(self, version):
        # Validate the version and parse it into pieces
        match = self._regex.search(version)
        if not match:
            raise InvalidVersion("Invalid version: '{0}'".format(version))

        # Store the parsed out pieces of the version
        self._version = _Version(
            epoch=int(match.group("epoch")) if match.group("epoch") else 0,
            release=tuple(int(i) for i in match.group("release").split(".")),
            pre=_parse_letter_version(
                match.group("pre_l"),
                match.group("pre_n"),
            ),
            post=_parse_letter_version(
                match.group("post_l"),
                match.group("post_n1") or match.group("post_n2"),
            ),
            dev=_parse_letter_version(
                match.group("dev_l"),
                match.group("dev_n"),
            ),
            local=_parse_local_version(match.group("local")),
        )

        # Generate a key which will be used for sorting
        self._key = _cmpkey(
            self._version.epoch,
            self._version.release,
            self._version.pre,
            self._version.post,
            self._version.dev,
            self._version.local,
        )

    def __repr__(self):
        return "<Version({0})>".format(repr(str(self)))

    def __str__(self):
        parts = []

        # Epoch
        if self._version.epoch != 0:
            parts.append("{0}!".format(self._version.epoch))

        # Release segment
        parts.append(".".join(str(x) for x in self._version.release))

        # Pre-release
        if self._version.pre is not None:
            parts.append("".join(str(x) for x in self._version.pre))

        # Post-release
        if self._version.post is not None:
            parts.append(".post{0}".format(self._version.post[1]))

        # Development release
        if self._version.dev is not None:
            parts.append(".dev{0}".format(self._version.dev[1]))

        # Local version segment
        if self._version.local is not None:
            parts.append(
                "+{0}".format(".".join(str(x) for x in self._version.local))
            )

        return "".join(parts)

    @property
    def public(self):
        return str(self).split("+", 1)[0]

    @property
    def local(self):
        version_string = str(self)
        if "+" in version_string:
            return version_string.split("+", 1)[1]

    @property
    def is_prerelease(self):
        return bool(self._version.dev or self._version.pre)


def _parse_letter_version(letter, number):
    if letter:
        # We consider there to be an implicit 0 in a pre-release if there is
        # not a numeral associated with it.
        if number is None:
            number = 0

        # We normalize any letters to their lower case form
        letter = letter.lower()

        # We consider some words to be alternate spellings of other words and
        # in those cases we want to normalize the spellings to our preferred
        # spelling.
        if letter == "alpha":
            letter = "a"
        elif letter == "beta":
            letter = "b"
        elif letter in ["rc", "pre", "preview"]:
            letter = "c"

        return letter, int(number)
    if not letter and number:
        # We assume if we are given a number, but we are not given a letter
        # then this is using the implicit post release syntax (e.g. 1.0-1)
        letter = "post"

        return letter, int(number)


_local_version_seperators = re.compile(r"[\._-]")


def _parse_local_version(local):
    """
    Takes a string like abc.1.twelve and turns it into ("abc", 1, "twelve").
    """
    if local is not None:
        return tuple(
            part.lower() if not part.isdigit() else int(part)
            for part in _local_version_seperators.split(local)
        )


def _cmpkey(epoch, release, pre, post, dev, local):
    # When we compare a release version, we want to compare it with all of the
    # trailing zeros removed. So we'll use a reverse the list, drop all the now
    # leading zeros until we come to something non zero, then take the rest
    # re-reverse it back into the correct order and make it a tuple and use
    # that for our sorting key.
    release = tuple(
        reversed(list(
            itertools.dropwhile(
                lambda x: x == 0,
                reversed(release),
            )
        ))
    )

    # We need to "trick" the sorting algorithm to put 1.0.dev0 before 1.0a0.
    # We'll do this by abusing the pre segment, but we _only_ want to do this
    # if there is not a pre or a post segment. If we have one of those then
    # the normal sorting rules will handle this case correctly.
    if pre is None and post is None and dev is not None:
        pre = -Infinity
    # Versions without a pre-release (except as noted above) should sort after
    # those with one.
    elif pre is None:
        pre = Infinity

    # Versions without a post segment should sort before those with one.
    if post is None:
        post = -Infinity

    # Versions without a development segment should sort after those with one.
    if dev is None:
        dev = Infinity

    if local is None:
        # Versions without a local segment should sort before those with one.
        local = -Infinity
    else:
        # Versions with a local segment need that segment parsed to implement
        # the sorting rules in PEP440.
        # - Alpha numeric segments sort before numeric segments
        # - Alpha numeric segments sort lexicographically
        # - Numeric segments sort numerically
        # - Shorter versions sort before longer versions when the prefixes
        #   match exactly
        local = tuple(
            (i, "") if isinstance(i, int) else (-Infinity, i)
            for i in local
        )

    return epoch, release, pre, post, dev, local


class InvalidSpecifier(ValueError):
    """
    An invalid specifier was found, users should refer to PEP 440.
    """


class Specifier(object):

    _regex = re.compile(
        r"""
        ^
        \s*
        (?P<operator>(~=|==|!=|<=|>=|<|>|===))
        (?P<version>
            (?:
                # The identity operators allow for an escape hatch that will
                # do an exact string match of the version you wish to install.
                # This will not be parsed by PEP 440 and we cannot determine
                # any semantic meaning from it. This operator is discouraged
                # but included entirely as an escape hatch.
                (?<====)  # Only match for the identity operator
                \s*
                [^\s]*    # We just match everything, except for whitespace
                          # since we are only testing for strict identity.
            )
            |
            (?:
                # The (non)equality operators allow for wild card and local
                # versions to be specified so we have to define these two
                # operators separately to enable that.
                (?<===|!=)            # Only match for equals and not equals

                \s*
                v?
                (?:[0-9]+!)?          # epoch
                [0-9]+(?:\.[0-9]+)*   # release
                (?:                   # pre release
                    [-_\.]?
                    (a|b|c|rc|alpha|beta|pre|preview)
                    [-_\.]?
                    [0-9]*
                )?
                (?:                   # post release
                    (?:-[0-9]+)|(?:[-_\.]?(post|rev|r)[-_\.]?[0-9]*)
                )?

                # You cannot use a wild card and a dev or local version
                # together so group them with a | and make them optional.
                (?:
                    (?:[-_\.]?dev[-_\.]?[0-9]*)?         # dev release
                    (?:\+[a-z0-9]+(?:[-_\.][a-z0-9]+)*)? # local
                    |
                    \.\*  # Wild card syntax of .*
                )?
            )
            |
            (?:
                # The compatible operator requires at least two digits in the
                # release segment.
                (?<=~=)               # Only match for the compatible operator

                \s*
                v?
                (?:[0-9]+!)?          # epoch
                [0-9]+(?:\.[0-9]+)+   # release  (We have a + instead of a *)
                (?:                   # pre release
                    [-_\.]?
                    (a|b|c|rc|alpha|beta|pre|preview)
                    [-_\.]?
                    [0-9]*
                )?
                (?:                                   # post release
                    (?:-[0-9]+)|(?:[-_\.]?(post|rev|r)[-_\.]?[0-9]*)
                )?
                (?:[-_\.]?dev[-_\.]?[0-9]*)?          # dev release
            )
            |
            (?:
                # All other operators only allow a sub set of what the
                # (non)equality operators do. Specifically they do not allow
                # local versions to be specified nor do they allow the prefix
                # matching wild cards.
                (?<!==|!=|~=)         # We have special cases for these
                                      # operators so we want to make sure they
                                      # don't match here.

                \s*
                v?
                (?:[0-9]+!)?          # epoch
                [0-9]+(?:\.[0-9]+)*   # release
                (?:                   # pre release
                    [-_\.]?
                    (a|b|c|rc|alpha|beta|pre|preview)
                    [-_\.]?
                    [0-9]*
                )?
                (?:                                   # post release
                    (?:-[0-9]+)|(?:[-_\.]?(post|rev|r)[-_\.]?[0-9]*)
                )?
                (?:[-_\.]?dev[-_\.]?[0-9]*)?          # dev release
            )
        )
        \s*
        $
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    _operators = {
        "~=": "compatible",
        "==": "equal",
        "!=": "not_equal",
        "<=": "less_than_equal",
        ">=": "greater_than_equal",
        "<": "less_than",
        ">": "greater_than",
        "===": "arbitrary",
    }

    def __init__(self, specs="", prereleases=None):
        # Split on comma to get each individual specification
        _specs = set()
        for spec in (s for s in specs.split(",") if s):
            match = self._regex.search(spec)
            if not match:
                raise InvalidSpecifier("Invalid specifier: '{0}'".format(spec))

            _specs.add(
                (
                    match.group("operator").strip(),
                    match.group("version").strip(),
                )
            )

        # Set a frozen set for our specifications
        self._specs = frozenset(_specs)

        # Store whether or not this Specifier should accept prereleases
        self._prereleases = prereleases

    def __repr__(self):
        return "<Specifier({0})>".format(repr(str(self)))

    def __str__(self):
        return ",".join(["".join(s) for s in sorted(self._specs)])

    def __hash__(self):
        return hash(self._specs)

    def __and__(self, other):
        if isinstance(other, string_types):
            other = Specifier(other)
        elif not isinstance(other, Specifier):
            return NotImplemented

        return self.__class__(",".join([str(self), str(other)]))

    def __eq__(self, other):
        if isinstance(other, string_types):
            other = Specifier(other)
        elif not isinstance(other, Specifier):
            return NotImplemented

        return self._specs == other._specs

    def __ne__(self, other):
        if isinstance(other, string_types):
            other = Specifier(other)
        elif not isinstance(other, Specifier):
            return NotImplemented

        return self._specs != other._specs

    def _get_operator(self, op):
        return getattr(self, "_compare_{0}".format(self._operators[op]))

    def _compare_compatible(self, prospective, spec):
        # Compatible releases have an equivalent combination of >= and ==. That
        # is that ~=2.2 is equivalent to >=2.2,==2.*. This allows us to
        # implement this in terms of the other specifiers instead of
        # implementing it ourselves. The only thing we need to do is construct
        # the other specifiers.

        # We want everything but the last item in the version, but we want to
        # ignore post and dev releases and we want to treat the pre-release as
        # it's own separate segment.
        prefix = ".".join(
            list(
                itertools.takewhile(
                    lambda x: (not x.startswith("post")
                               and not x.startswith("dev")),
                    _version_split(spec),
                )
            )[:-1]
        )

        # Add the prefix notation to the end of our string
        prefix += ".*"

        return (self._get_operator(">=")(prospective, spec)
                and self._get_operator("==")(prospective, prefix))

    def _compare_equal(self, prospective, spec):
        # We need special logic to handle prefix matching
        if spec.endswith(".*"):
            # Split the spec out by dots, and pretend that there is an implicit
            # dot in between a release segment and a pre-release segment.
            spec = _version_split(spec[:-2])  # Remove the trailing .*

            # Split the prospective version out by dots, and pretend that there
            # is an implicit dot in between a release segment and a pre-release
            # segment.
            prospective = _version_split(str(prospective))

            # Shorten the prospective version to be the same length as the spec
            # so that we can determine if the specifier is a prefix of the
            # prospective version or not.
            prospective = prospective[:len(spec)]

            # Pad out our two sides with zeros so that they both equal the same
            # length.
            spec, prospective = _pad_version(spec, prospective)
        else:
            # Convert our spec string into a Version
            spec = Version(spec)

            # If the specifier does not have a local segment, then we want to
            # act as if the prospective version also does not have a local
            # segment.
            if not spec.local:
                prospective = Version(prospective.public)

        return prospective == spec

    def _compare_not_equal(self, prospective, spec):
        return not self._compare_equal(prospective, spec)

    def _compare_less_than_equal(self, prospective, spec):
        return prospective <= Version(spec)

    def _compare_greater_than_equal(self, prospective, spec):
        return prospective >= Version(spec)

    def _compare_less_than(self, prospective, spec):
        # Less than are defined as exclusive operators, this implies that
        # pre-releases do not match for the same series as the spec. This is
        # implemented by making <V imply !=V.*.
        return (prospective < Version(spec)
                and self._get_operator("!=")(prospective, spec + ".*"))

    def _compare_greater_than(self, prospective, spec):
        # Greater than are defined as exclusive operators, this implies that
        # pre-releases do not match for the same series as the spec. This is
        # implemented by making >V imply !=V.*.
        return (prospective > Version(spec)
                and self._get_operator("!=")(prospective, spec + ".*"))

    def _compare_arbitrary(self, prospective, spec):
        return str(prospective).lower() == str(spec).lower()

    @property
    def prereleases(self):
        # If there is an explicit prereleases set for this, then we'll just
        # blindly use that.
        if self._prereleases is not None:
            return self._prereleases

        # Look at all of our specifiers and determine if they are inclusive
        # operators, and if they are if they are including an explicit
        # prerelease.
        for spec, version in self._specs:
            if spec in ["==", ">=", "<=", "~="]:
                # The == specifier can include a trailing .*, if it does we
                # want to remove before parsing.
                if spec == "==" and version.endswith(".*"):
                    version = version[:-2]

                # Parse the version, and if it is a pre-release than this
                # specifier allows pre-releases.
                if parse(version).is_prerelease:
                    return True

        return False

    @prereleases.setter
    def prereleases(self, value):
        self._prereleases = value

    def contains(self, item, prereleases=None):
        # Determine if prereleases are to be allowed or not.
        if prereleases is None:
            prereleases = self.prereleases

        # Normalize item to a Version or LegacyVersion, this allows us to have
        # a shortcut for ``"2.0" in Specifier(">=2")
        if isinstance(item, (Version, LegacyVersion)):
            version_item = item
        else:
            try:
                version_item = Version(item)
            except ValueError:
                version_item = LegacyVersion(item)

        # Determine if we should be supporting prereleases in this specifier
        # or not, if we do not support prereleases than we can short circuit
        # logic if this version is a prereleases.
        if version_item.is_prerelease and not prereleases:
            return False

        # Detect if we have any specifiers, if we do not then anything matches
        # and we can short circuit all this logic.
        if not self._specs:
            return True

        # If we're operating on a LegacyVersion, then we can only support
        # arbitrary comparison so do a quick check to see if the spec contains
        # any non arbitrary specifiers
        if isinstance(version_item, LegacyVersion):
            if any(op != "===" for op, _ in self._specs):
                return False

        # Ensure that the passed in version matches all of our version
        # specifiers
        return all(
            self._get_operator(op)(
                version_item if op != "===" else item,
                spec,
            )
            for op, spec, in self._specs
        )

    def filter(self, iterable, prereleases=None):
        iterable = list(iterable)
        yielded = False
        found_prereleases = []

        kw = {"prereleases": prereleases if prereleases is not None else True}

        # Attempt to iterate over all the values in the iterable and if any of
        # them match, yield them.
        for version in iterable:
            if not isinstance(version, (Version, LegacyVersion)):
                parsed_version = parse(version)
            else:
                parsed_version = version

            if self.contains(parsed_version, **kw):
                # If our version is a prerelease, and we were not set to allow
                # prereleases, then we'll store it for later incase nothing
                # else matches this specifier.
                if (parsed_version.is_prerelease
                        and not (prereleases or self.prereleases)):
                    found_prereleases.append(version)
                # Either this is not a prerelease, or we should have been
                # accepting prereleases from the begining.
                else:
                    yielded = True
                    yield version

        # Now that we've iterated over everything, determine if we've yielded
        # any values, and if we have not and we have any prereleases stored up
        # then we will go ahead and yield the prereleases.
        if not yielded and found_prereleases:
            for version in found_prereleases:
                yield version


_prefix_regex = re.compile(r"^([0-9]+)((?:a|b|c|rc)[0-9]+)$")


def _version_split(version):
    result = []
    for item in version.split("."):
        match = _prefix_regex.search(item)
        if match:
            result.extend(match.groups())
        else:
            result.append(item)
    return result


def _pad_version(left, right):
    left_split, right_split = [], []

    # Get the release segment of our versions
    left_split.append(list(itertools.takewhile(lambda x: x.isdigit(), left)))
    right_split.append(list(itertools.takewhile(lambda x: x.isdigit(), right)))

    # Get the rest of our versions
    left_split.append(left[len(left_split):])
    right_split.append(left[len(right_split):])

    # Insert our padding
    left_split.insert(
        1,
        ["0"] * max(0, len(right_split[0]) - len(left_split[0])),
    )
    right_split.insert(
        1,
        ["0"] * max(0, len(left_split[0]) - len(right_split[0])),
    )

    return (
        list(itertools.chain(*left_split)),
        list(itertools.chain(*right_split)),
    )
