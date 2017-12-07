
"""Extend ``ConfigParser`` to add some inheritance functionality."""

import configparser
import collections

DEFAULT_ZSEP = ' : '
REVERSED = ('.',)


class ZDictError(Exception):
    """Base class for `ZDict` Exceptions."""


class ZKeyError(ZDictError, KeyError):
    """Raised when no zkey is found."""

    def __init__(self, key):
        msg = "No key %r found in shortnames and longnames." % (key,)
        super().__init__(msg)


class DuplicateZKeyError(ZDictError):
    """Raised when duplicate zkeys are found."""

    def __init__(self, new, old):
        msg = "Duplicate zkeys: %r. %r already exists." % (new, old)
        super().__init__(msg)


class RecursiveZkeyError(ZDictError):
    """Raised when circular zkey structure is found.

    cf. '[aa : bb]', '[bb : cc]', '[cc : aa]'
    """

    def __init__(self, key):
        msg = "Recurcive zkey detected: %r." % (key,)
        super().__init__(msg)


class Error(Exception):
    """Base class for `ZConfigParser` Exceptions."""


class NoZSectionError(Error, configparser.NoSectionError):
    """Raised when no zsection is found."""

    def __init__(self, section):
        super().__init__('No zsection: %r' % (section,))


class NoZOptionError(Error, configparser.NoOptionError):
    """Raised when no option in a zsection is found."""

    def __init__(self, option):
        super().__init__('No zoption: %r' % (option,))


# not used
# class DuplicateZSectionError(Error, configparser.DuplicateSectionError):
#     """Raised when duplicate zsections are found.

#     cf. `ConfigParser.DuplicateSectionError` provides
#     'source' and 'lineno' information when reading from a file.
#     """


class ZDict(collections.OrderedDict):
    """A custom dictionary used in `ZConfigParser`.

    It creates and keeps internal zsection dependency dictionaries.
    (They are ordinary ``dict``).
    Without this, `ZConfigParser` has to search all sections all the time
    and is very slow.
    """

    def __init__(self, *args, **kwargs):
        self.ZSEP = kwargs.pop('ZSEP', DEFAULT_ZSEP)
        self.zdata = dict()
        self._zparents = dict()    # used for valification
        super().__init__(*args, **kwargs)

    def _zsplit(self, key):
        keys = key.split(self.ZSEP)
        if self.ZSEP in REVERSED:
            keys.reverse()
        return keys

    def _zkey(self, key):
        if key in self:
            return key
        if key in self.zdata:
            return self.zdata[key]
        raise ZKeyError(key)

    def _get_shortnames(self, key, collected=None):
        if collected is None:
            collected = []
        longname = self._zkey(key)
        shortnames = self._zsplit(longname)
        shortname = shortnames[0]
        if shortname in collected:
            raise RecursiveZkeyError(shortname)
        collected.append(shortname)
        if len(shortnames) > 1:
            for key in shortnames[1:]:
                self._get_shortnames(key, collected)
        return collected

    def __setitem__(self, key, value):
        """When setting, the dictionary memorizes zsections structure.

        Keys must be longnames.
        Used when `ConfigParser` reads files, dicts, etc..
        """
        shortnames = self._zsplit(key)
        shortname = shortnames[0]
        if len(shortnames) > 1:
            old = self._zparents.get(shortname)
            if old and not old == shortnames:
                raise DuplicateZKeyError(shortnames, old)
            self.zdata[shortname] = key
            self._zparents[shortname] = shortnames
        super().__setitem__(key, value)

    def zget(self, key):
        all_shortnames = self._get_shortnames(key)
        longnames = [self._zkey(s) for s in all_shortnames]
        values = [self[lo] for lo in longnames]
        return values

    def zkeys(self):
        """Collect all shortnames and longnames.

        Two dictionary keys are combined (sections and zsections),
        so key ordering of `OrderedDict` part is not preserved.
        """
        # `KeysView` is subclass of `set`.
        keys = self.keys() | self.zdata.keys()
        return collections.abc.KeysView(keys)

    def zcontains(self, key):
        return key in self.zkeys()

    def __repr__(self):
        return super().__repr__()


class ZDictGen(object):
    """A supplement class needed to create `ZSEP` pre-initialized `ZDict`.

    To adjust for `ConfigParser` intialization argument `dict_type`.
    """

    def __init__(self, *args, **kwargs):
        self._ZSEP = kwargs.pop('ZSEP', DEFAULT_ZSEP)
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        return ZDict(*self._args, ZSEP=self._ZSEP, **self._kwargs)


class ZConfigParser(configparser.ConfigParser):
    """ConfigParser, plus some section inheritance function.

    E.g. section ``[aa : bb]`` becomes ``[aa]``,
    and inherits and overrides section [bb].
    Default separator word is ' : ', exactly one space before and after ':'.
    """

    def __init__(self, *args, **kwargs):
        if len(args) > 1 or 'dict_type' in kwargs:
            msg = ("you can not assign 'dict_type' in ZConfigParser")
            raise ValueError(msg)
        self.ZSEP = kwargs.pop('ZSEP', DEFAULT_ZSEP)
        zd = ZDictGen(ZSEP=self.ZSEP)
        super().__init__(*args, dict_type=zd, **kwargs)

    def get(self, section, option, **kwargs):
        """Override `ConfigParser`'s method.

        `ZConfigParser` only wraps Exceptions in `get`.
        Other 'get' (`getint` etc.)
        might leak (raise) `ConfigParser`'s Exceptions.
        """
        try:
            return super().get(section, option, **kwargs)
        except configparser.NoSectionError:
            raise NoZSectionError(section)
        except configparser.NoOptionError:
            raise NoZOptionError(option)

    def _unify_values(self, section, vars):
        """Override `ConfigParser`'s method.

        ConfigParser's `.get()` calls this function.
        The code is mostly the same as the original,
        just inserting dictionaries list,
        instead of a dictionary (sectiondict).
        """
        sectiondict = [{}]
        try:
            sectiondict = self._sections.zget(section)
        except ZKeyError:
            if section != self.default_section:
                raise NoZSectionError(section)

        vardict = {}
        if vars:
            for key, value in vars.items():
                if value is not None:
                    value = str(value)
                vardict[self.optionxform(key)] = value
        return collections.ChainMap(vardict, *sectiondict, self._defaults)

    def zsections(self):
        """Return all section shortnames and longnames."""
        return self._sections.zkeys()

    def has_zsection(self, section):
        """Check section name (whether short or long)."""
        return self._sections.zcontains(section)

    def has_zoption(self, section, option):
        """Check option name in a zsection (whether short or long)."""
        try:
            self.get(section, option)
            return True
        except (NoZSectionError, NoZOptionError, ZKeyError):
            return False
