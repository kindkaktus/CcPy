"""Enumerated type support in Python

Originally taken from http://cheeseshop.python.org/pypi/enum/ version 0.4.4

An enumeration object is created with a sequence of string arguments
to the Enum() constructor::

    >>> from enum import Enum
    >>> clrs = Enum('red', 'green','blue')

The return value is an immutable sequence object with a value for each
of the string arguments. Each value is also available as an attribute
named from the corresponding string argument::

    >>> green = clrs.green

Each enumeration is entirely defined by the sequence of its arguments.

    >>> same_clrs = Enum('red', 'green','blue')
    >>> same_clrs == clrs
    True
    >>> another_clrs = Enum('red', 'blue', 'green')
    >>> another_clrs == clrs
    False

The values are constants that can be compared only with values from
the same enumeration (i.e. enums created with the same set of args);
comparison with other values will invoke Python's fallback comparisons. :

    >>> green == clrs.green
    True
    >>> green > clrs.red
    True
    >>> clrs.green > same_clrs.green
    True
    >>> green == another_clrs.green
    False
    >>> from copy import deepcopy
    >>> clrs.green == deepcopy(clrs.green)
    True


This was a major (breaking) change wrt the original implementation:
the same enum values from the enums created with the same args are equal.
Deepcopying of the enum value produces the same enum value.

Each value is accessible by index or by its string value

    >>> red = clrs[0]
    >>> red = clrs['red']

Each value from an enumeration exports its sequence index
as an integer, and can be coerced to a simple string matching the
original arguments used to create the enumeration::

    >>> str(green)
    'green'
    >>> green.index
    1

Remarks: this implementation simulates a certain enum type as
a class instance. This explains the decision to identify
a certain enum (= type) solely by the sequence of its enum values
(= class instance data attributes).
"""


class EnumException(Exception):

    """ Base class for all exceptions in this module """

    def __init__(self):
        if self.__class__ is EnumException:
            raise NotImplementedError("%s is an abstract class for subclassing" % self.__class__)


class EnumEmptyError(AssertionError, EnumException):

    """ Raised when attempting to create an empty enumeration """

    def __str__(self):
        return "Enumerations cannot be empty"


class EnumBadKeyError(TypeError, EnumException):

    """ Raised when creating an Enum with non-string keys """

    def __init__(self, key):
        self.key = key

    def __str__(self):
        return "Enumeration keys must be strings: %s" % (self.key,)


class EnumImmutableError(TypeError, EnumException):

    """ Raised when attempting to modify an Enum """

    def __init__(self, *args):
        self.args = args

    def __str__(self):
        return "Enumeration does not allow modification"


class ComparableMixin(object):

    def __eq__(self, other):
        return not self < other and not other < self

    def __ne__(self, other):
        return self < other or other < self

    def __gt__(self, other):
        return other < self

    def __ge__(self, other):
        return not self < other

    def __le__(self, other):
        return not other < self


class _EnumValue(ComparableMixin):

    """ A specific value of an enumerated type """

    def __init__(self, enumHash, index, key):
        self.__enumHash = enumHash
        self.__index = index
        self.__key = key

    @property
    def enumHash(self):
        return self.__enumHash

    @property
    def key(self):
        return self.__key

    @property
    def index(self):
        return self.__index

    def __str__(self):
        return "%s" % (self.key)

    def __repr__(self):
        return "EnumValue(%s, %s, %s)" % (repr(
            self.__enumHash),
            repr(
            self.__index),
            repr(
            self.__key))

    def __hash__(self):
        return hash(self.__index)

    def __lt__(self, other):
        if self.enumHash == other.enumHash:
            return self.index < other.index
        return NotImplementedError("Cannot compare objects with different hashes")
    # for Python 2.x

    def __cmp__(self, other):
        if self.enumHash == other.enumHash:
            return cmp(self.index, other.index)
        return NotImplementedError("Cannot compare objects with different hashes")


class Enum(ComparableMixin):

    """ Enumerated type """

    def __init__(self, *keys):
        if not keys:
            raise EnumEmptyError()
        keys = list(keys)
        super(Enum, self).__setattr__('_keys', keys)
        myHash = hash(self)
        values = [None] * len(keys)

        for i, key in enumerate(keys):
            value = _EnumValue(myHash, i, key)
            values[i] = value
            try:
                super(Enum, self).__setattr__(key, value)
            except TypeError as e:
                raise EnumBadKeyError(key)
        super(Enum, self).__setattr__('_values', values)

    @staticmethod
    def _is_string(obj):
        try:
            return isinstance(obj, basestring)
        except NameError:  # means we use python2 because there is no basestring in python3
            return isinstance(obj, str)

    def __setattr__(self, name, value):
        raise EnumImmutableError(name)

    def __delattr__(self, name):
        raise EnumImmutableError(name)

    def __len__(self):
        return len(self._values)

    def __getitem__(self, key_or_index):
        if Enum._is_string(key_or_index):
            keyStr = key_or_index
            index = self._keys.index(keyStr)
        else:
            index = key_or_index
        return self._values[index]

    def __setitem__(self, index, value):
        raise EnumImmutableError(index)

    def __delitem__(self, index):
        raise EnumImmutableError(index)

    def __iter__(self):
        return iter(self._values)

    def __contains__(self, value):
        is_member = False
        if Enum._is_string(value):
            is_member = (value in self._keys)
        else:
            try:
                is_member = (value in self._values)
            except BaseException:
                pass
        return is_member

    def __hash__(self):
        return hash(",".join(self._keys))

    def __lt__(self, other):
        return hash(self) < hash(other)

    # for Python 2.x
    def __cmp__(self, other):
        return cmp(hash(self), hash(other))
