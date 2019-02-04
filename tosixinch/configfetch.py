
"""Helper to get values from configparser and argparse."""

import argparse
from collections import OrderedDict
import configparser
import os
import re
import shlex
import sys

_UNSET = object()

# Record available function names for value conversions.
# After the module initialization, this list is populated.
_REGISTRY = set()


class Error(Exception):
    """Base Exception class for the module.

    ``configparser`` has 11 custom Exceptions scattered in 14 methods
    last time I checked.
    I'm not going to wrap except the most relevant ones.
    """


class NoSectionError(Error, configparser.NoSectionError):
    """Raised when no section is found."""


class NoOptionError(Error, configparser.NoOptionError):
    """Raised when no option is found."""

    def __init__(self, option, section):
        super().__init__(option, section)


def register(meth):
    """Decorate value functions to populate global value `_REGISTRY`."""
    _REGISTRY.add(meth.__name__)
    return meth


def _func_dict(registry):
    """Make a dictionary with uppercase keys.

    E.g. ``_comma`` to ``{'COMMA': '_comma'}``
    """
    return {func.lstrip('_').upper(): func for func in registry}


def _func_regex(registry):
    r"""Make regex expression to parse conversion syntax.

    Custom option format is e.g. ``users = [=COMMA] alice, bob, charlie``.
    We parse '[=COMMA]', strip this, record ``option -> conversion`` map.

    So e.g. ``['_comma', '_bar']`` should change to
    ``(?:[=(COMMA)]|[=(BAR)])\s*``.
    """
    formats = _func_dict(registry).keys()
    formats = '|'.join([r'\[=(' + fmt + r')\]' for fmt in formats])
    formats = r'\s*(?:' + formats + r')\s*'
    return re.compile(formats)


def _parse_comma(value):
    if value:
        return [val.strip()
                for val in value.split(',') if val.strip()] or []
    return []


def _parse_line(value):
    if value:
        return [val.strip(' ,')
                for val in value.split('\n') if val.strip()] or []
    return []


class Func(object):
    """Register and apply value conversions."""

    BOOLEAN_STATES = {
        '1': True, 'yes': True, 'true': True, 'on': True,
        '0': False, 'no': False, 'false': False, 'off': False}

    def __init__(self, ctx, fmts):
        self._ctx = ctx
        self._fmts = fmts

    @register
    def _bool(self, value):
        # It is the same as `ConfigParser`'s ``_convert_to_boolean``.
        if value.lower() not in self.BOOLEAN_STATES:
            raise ValueError('Not a boolean: %s' % value)
        return self.BOOLEAN_STATES[value.lower()]

    @register
    def _comma(self, value):
        return _parse_comma(value)

    @register
    def _line(self, value):
        return _parse_line(value)

    @register
    def _bar(self, value):
        """Connect values with ``bar`` (``'|'``).

        Presupose that 'value' is a list,
        already processed by other functions.
        Blank strings list (like ['', ' ', '  ']) evaluates to ''.
        """
        if not isinstance(value, list):
            msg = "'configfetch.Func._bar()' accepts only 'list'. Got %r"
            raise ValueError(msg % str(value))
        if any(value):
            return '|'.join(value)
        else:
            return ''

    @register
    def _cmd(self, value):
        return shlex.split(value, comments='#')

    @register
    def _fmt(self, value):
        """Evaluate part of value, using `str.format`.

        Modify ``{USER}/data/my.css`` to e.g. ``/home/john/data/my.css``,
        according to ``fmts`` dictionary.
        Blank string ('') returns blank string.
        """
        return value.format(**self._fmts)

    @register
    def _plus(self, value):
        """Implement ``plusminus option`` (my neologism).

        Main logic is in `_get_plusminus_values`.
        Presuppose values are not processed.
        """
        values = self.values
        return _get_plusminus_values(reversed(values))

    def _get_value(self, values):
        arg, env, conf = values
        if arg not in (_UNSET, None):
            value = arg
        elif env not in (_UNSET, ''):
            value = env
        elif conf is not _UNSET:
            value = conf
        else:
            value = _UNSET
        return value

    def _get_funcname(self, option):
        funcdict = _func_dict(_REGISTRY)
        funcnames = []
        if self._ctx:
            if self._ctx.get(option):
                for f in self._ctx.get(option).split(','):
                    f = f.strip()
                    funcnames.append(funcdict[f])
        return funcnames

    def _get_func(self, option):
        funcnames = self._get_funcname(option)
        return [getattr(self, fn) for fn in funcnames]

    def _format_value(self, option, values, func):
        value = self._get_value(values)
        if value is _UNSET:
            raise NoOptionError(option, self._ctx.name)
        if not func:
            return value
        for f in func:
            value = f(value)
        return value

    def __call__(self, option, values):
        func = self._get_func(option)
        self.values = values
        value = self._format_value(option, values, func)
        return value


class ConfigLoad(object):
    """A custom Configuration builder.

    Read from custom config file with some additional information
    and launch ConfigParser.

    You can pass ``parser``'s keyword argumants in initializing.
    additional arguments are:

    :param cfile: custom ini format filename or string
    :param parser: returned object by `__call__`,
        configparser.ConfigParser (default) or similar object

    Furthermore, if you use this class for ``ConfigFetch``,
    small parser customizetions are needed.

    * If you use dot access (e.g. ``obj.attribute``),
      'dash' must be changed to 'underscore',
      to make the key to identifier.
    * Default ``configparser`` converts all option names to lowercase.
      Disable this, for ``ArgumentParser`` might use uppercases.

    :param use_dash: default True (changes dashes to underscores internally)
    :param use_uppercase: default True
    """

    def __init__(self, *args, **kwargs):
        cfile = kwargs.pop('cfile', None)
        parser = kwargs.pop('parser', configparser.ConfigParser)
        use_dash = kwargs.pop('use_dash', True)
        use_uppercase = kwargs.pop('use_uppercase', True)
        optionxform = self._optionxform(use_dash, use_uppercase)

        config = parser(*args, **kwargs)
        config.optionxform = optionxform
        if os.path.exists(cfile):
            with open(cfile) as f:
                config.read_file(f)
        else:
            config.read_string(cfile)

        # ctxs(contexts) is also a ConfigParser object, not just a dictionary,
        # because of ``default_section`` handling.
        ctxs = configparser.ConfigParser(
            default_section=config.default_section)
        ctxs.optionxform = config.optionxform
        for secname, section in config.items():
            if not secname == ctxs.default_section:
                ctxs.add_section(secname)
            ctx = ctxs[secname]
            for option in section:
                self._parse_format(section, option, ctx)

        self._config = config
        self._ctxs = ctxs

    def _optionxform(self, use_dash, use_uppercase):
        def _xform(option):
            if use_dash:
                option = option.replace('-', '_')
            if not use_uppercase:
                option = option.lower()
            return option
        return _xform

    def _parse_format(self, section, option, ctx):
        value = section[option]
        func_regex = _func_regex(_REGISTRY)

        func = []
        while True:
            match = func_regex.match(value)
            if match:
                # ``match.groups()`` should be ``None``'s except one.
                f = [g for g in match.groups() if g][0]
                func.append(f)
                value = value[match.end():]
            else:
                break

        section[option] = value
        if func:
            # ``ctxs`` is a ``configparser`` object,
            # so option values must be a string.
            ctx[option] = ','.join(func)

    def __call__(self):
        return self._config, self._ctxs


class ConfigFetch(object):
    """``ConfigParser`` proxy object with dot access.

    Actual work is delegated to `SectionFetch`.
    """

    def __init__(self, config, ctxs=None,
            fmts=None, args=None, envs=None, Func=Func):
        self._config = config
        self._ctxs = ctxs or {}
        self._fmts = fmts or {}
        self._args = args or argparse.Namespace()
        self._envs = envs or {}
        self._Func = Func
        self._cache = {}

        # shortcut
        self.read = self._config.read

    # TODO:
    # Invalidate section names this class reserves.

    # cf.
    # >>> for a in dir(c.fetch('')): print(a)

    # cf.
    # >>> for m in inspect.getmembers(c.fetch('')): print(m)
    # got the error somehow
    # ``configfetch.NoSectionError: No section: '__bases__'``
    def __getattr__(self, section):
        if section in self._cache:
            return self._cache[section]

        if section in self._ctxs:
            ctx = self._ctxs[section]
        else:
            ctx = self._ctxs[self._ctxs.default_section]

        s = SectionFetch(
            self, section, ctx, self._fmts, self._Func)
        self._cache[section] = s
        return s

    def get(self, section):
        try:
            return self.__getattr__(section)
        except NoSectionError:
            # follows dictionary's ``.get()``
            return None

    def __iter__(self):
        return self._config.__iter__()


class SectionFetch(object):
    """``ConfigParser`` section proxy object.

    Similar to ``ConfigParser``'s proxy object itself.
    Also access ``ArgumentParser`` arguments and environment variables.
    """

    def __init__(self, conf, section, ctx, fmts, Func):
        self._conf = conf
        self._config = conf._config
        self._section = section
        self._ctx = ctx
        self._fmts = fmts
        self._Func = Func

        # 'ConfigParser.__contains__()' includes default section.
        if self._get_section() not in self._config:
            raise NoSectionError(self._get_section())

    # Introduce small indirection,
    # in case it needs special section manipulation in user subclasses.
    # ``None`` option case must be provided
    # for section verification in `__init__()`.
    def _get_section(self, option=None):
        return self._section

    def _get_conf(self, option, fallback=_UNSET, convert=False):
        section = self._get_section(option)
        try:
            value = self._config.get(section, option)
        except configparser.NoOptionError:
            return fallback

        if convert:
            value = self._convert(option, (value, _UNSET, _UNSET))
        return value

    def _get_arg(self, option):
        if self._conf._args and option in self._conf._args:
            return getattr(self._conf._args, option)
        return _UNSET

    def _get_env(self, option):
        env = None
        if self._conf._envs and option in self._conf._envs:
            env = self._conf._envs[option]
        if env and env in os.environ:
            return os.environ[env]
        return _UNSET

    def _get_values(self, option):
        return [self._get_arg(option),
                self._get_env(option),
                self._get_conf(option)]

    def __getattr__(self, option):
        values = self._get_values(option)
        return self._convert(option, values)

    def _convert(self, option, values):
        # ``arg`` may have non-string value.
        # it returns it as is (not raising Error).
        arg = values[0]
        if arg not in (_UNSET, None):
            if not isinstance(arg, str):
                return arg
        f = self._get_func()
        return f(option, values)

    def _get_funcname(self, option):
        f = self._get_func()
        return f._get_funcname(option)

    def _get_func(self):
        return self._Func(self._ctx, self._fmts)

    def get(self, option, fallback=_UNSET):
        try:
            return self.__getattr__(option)
        except NoOptionError:
            if fallback is _UNSET:
                raise
            else:
                return fallback

    # Note it does not do any reverse-formatting.
    def set_value(self, option, value):
        section = self._get_section(option)
        self._config.set(section, option, value)

    def __iter__(self):
        return self._config[self._section].__iter__()


class Double(object):
    """A utility class to parse two ``SectionFetch`` objects.

    To supply some secion an additional external section fallback.
    """

    def __init__(self, sec, parent_sec):
        self.sec = sec
        self.parent_sec = parent_sec

    def __getattr__(self, option):
        funcnames = self.sec._get_funcname(option)
        if funcnames == ['_plus']:
            return self._get_plus_value(option)
        else:
            return self._get_value(option)

    def _get_value(self, option):
        # Blank values are None, '', and []. 'False' should be excluded.

        # spec:
        # No preference between blank values. Just returns parent one.
        try:
            val = self.sec.get(option)
        except NoOptionError:
            parent_val = self.parent_sec.get(option)
            return parent_val

        if val in (None, '', []):
            try:
                parent_val = self.parent_sec.get(option)
                return parent_val
            except NoOptionError:
                pass

        return val

    def _get_plus_value(self, option):
        parent_val = self.parent_sec._get_conf(option)
        values = self.sec._get_values(option)
        values = values + [parent_val]
        self._check_unset(values, option, self.sec._ctx.name)
        return _get_plusminus_values(reversed(values))

    def get(self, option, fallback=_UNSET):
        try:
            return self.__getattr__(option)
        except ValueError:
            if fallback is _UNSET:
                raise
            else:
                return fallback

    def _check_unset(self, values, section, option):
        if all([value is _UNSET for value in values]):
            raise NoOptionError(section, option)

    def __iter__(self):
        return self.sec.__iter__()


def fetch(cfile, *, fmts=None, args=None, envs=None, Func=Func,
        parser=configparser.ConfigParser,
        use_dash=True, use_uppercase=True, **kwargs):
    """Fetch ``ConfigFetch`` object.

    It is a convenience function for the basic use of the library.
    """
    config, ctxs = ConfigLoad(cfile=cfile, parser=parser,
            use_dash=use_dash, use_uppercase=use_uppercase)()
    conf = ConfigFetch(config, ctxs, fmts, args, envs, Func)
    return conf


def _get_plusminus_values(adjusts, initial=None):
    """Add or sbtract values partially (used by ``_plus()``).

    Use ``+`` and ``-`` as the markers.

    Internally, the values list is converted to ``OrderedDict`` keys,
    with each dict value is ``None``,
    used as a substitute for 'Ordered Set'.
    """
    def _fromkeys(keys):
        return OrderedDict.fromkeys(keys)

    values = _fromkeys(initial) if initial else _fromkeys([])

    for adjust in adjusts:
        # if not adjust:
        if adjust in (_UNSET, None, '', []):
            continue
        if not isinstance(adjust, str):
            fmt = 'Each input should be a string. Got %r(%r)'
            raise ValueError(fmt % (type(adjust), str(adjust)))
        adjust = _parse_comma(adjust)

        if not any([a.startswith(('+', '-')) for a in adjust]):
            values = _fromkeys(adjust)
            continue

        for a in adjust:
            cmd, a = a[:1], a[1:]
            if a and cmd == '+':
                if a not in values:
                    values[a] = None
            elif a and cmd == '-':
                if a in values:
                    del values[a]
            else:
                fmt = ('Input members must be '
                    "'+something' or '-something', or none of them. Got %r.")
                raise ValueError(fmt % (cmd + a))
    return list(values.keys())


def minusadapter(parser, matcher=None, args=None):
    """Parse and edit commandline arguments.

    An accessory helper function.
    It unites two arguments to one, if the second argument starts with ``-``.

    | e.g. ``['--aa', '-somearg']`` becomes ``['--aa=-somearg']``.
    | e.g. ``['-a', '-somearg']`` becomes ``['-a-somearg']``.

    The reason is that ``argparse`` cannot parse this particular pattern.
    https://bugs.python.org/issue9334
    https://stackoverflow.com/a/21894384
    And `_plus` uses this type of arguments frequantly.

    :param parser: ArgumentParser object
    :param matcher: regex string to match options
    :param args: arguments list to parse, defaults to ``sys.argv[1:]``
    """
    def _iter_args(args, actions):
        args = iter(args)
        for arg in args:
            if arg in actions:
                if '=' not in arg:
                    try:
                        val = next(args)
                    except StopIteration:
                        yield arg
                        raise
                    if val.startswith('-'):
                        if arg.startswith('--'):
                            yield '%s=%s' % (arg, val)
                            continue
                        elif arg.startswith('-'):
                            yield '%s%s' % (arg, val)
                            continue
                    else:
                        yield arg
                        yield val
                        continue
            yield arg

    if not parser.prefix_chars == '-':
        return args

    actions = []
    classes = (argparse._StoreAction, argparse._AppendAction)
    for a in parser._actions:
        if isinstance(a, classes):
            if a.nargs in (1, None):
                for opt in a.option_strings:
                    if matcher:
                        if not re.match(matcher, opt):
                            continue
                    actions.append(opt)

    args = args if args else sys.argv[1:]
    return list(_iter_args(args, actions))
