
"""Helper to get values from configparser and argparse."""

import argparse
from collections import OrderedDict
import configparser
import os
import re
import shlex
import sys

# Record available function names for value conversions.
# After the module initialization, this list is populated.
_REGISTRY = set()

_UNSET = object()

# ConfigParser.BOOLEAN_STATES and ``None``
BOOLEAN_STATES = {
    '1': True, 'yes': True, 'true': True, 'on': True,
    '0': False, 'no': False, 'false': False, 'off': False,
    '': None,
}

_STRING_RE = re.compile(r"""(["'])(.+)\1$""")


class Error(Exception):
    """Base Exception class for the module."""


# ``configparser`` has 11 custom Exceptions scattered in 14 methods,
# the last time I checked.
# I'm not going to wrap except the most relevant ones.

class NoSectionError(Error, configparser.NoSectionError):
    """Raised when no section is found."""


class NoOptionError(Error, configparser.NoOptionError):
    """Raised when no option is found."""

    def __init__(self, option, section):
        super().__init__(option, section)


class OptionParseError(Error):
    """Raised when config has a invalid line."""


def register(meth):
    """Decorate value functions to populate global value `_REGISTRY`."""
    _REGISTRY.add(meth.__name__)
    return meth


def _parse_bool(value):
    value = value.lower()
    if value not in BOOLEAN_STATES:
        raise ValueError('Not a boolean: %s' % value)
    return BOOLEAN_STATES[value]


# following Mohammad Azim's advice
# https://stackoverflow.com/a/43137914
def _escaped_split(string, char):
    out = []
    part = []
    escape = False
    for c in string:
        if c == char:
            if escape:
                part[-1] = c  # pop the last character ('\\'), and add 'char'
            else:
                out.append(part)
                part = []
        else:
            part.append(c)
        escape = (c == '\\')
    if part:
        out.append(part)
    return [''.join(part) for part in out]


def _parse_comma(value):
    return [v.strip() for v in _escaped_split(value, ',') if v.strip()]


def _parse_line(value):
    return [v.strip() for v in _escaped_split(value, '\n') if v.strip()]


class Func(object):
    """Register and apply value conversions."""

    def __init__(self, name, ctx, fmts):
        self.name = name
        self._ctx = ctx
        self._fmts = fmts

    @register
    def bool(self, value):
        return _parse_bool(value)

    @register
    def comma(self, value):
        return _parse_comma(value)

    @register
    def line(self, value):
        return _parse_line(value)

    @register
    def bar(self, value):
        """Concatenate with ``'|'``.

        Receive a list of strings as ``value``, return a string.
        """
        if not isinstance(value, list):
            msg = "'configfetch.Func._bar()' accepts only 'list'. Got %r"
            raise ValueError(msg % str(value))
        if any(value):
            return '|'.join(value)
        else:
            return ''

    @register
    def cmd(self, value):
        """Return a list of strings, useful for ``subprocess`` (stdlib)."""
        return shlex.split(value, comments='#')

    @register
    def cmds(self, value):
        """List version of ``_cmd``."""
        return [self.cmd(v) for v in value]

    @register
    def fmt(self, value):
        """Return a string processed by ``str.format``."""
        return value.format(**self._fmts)

    @register
    def plus(self, value):
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
        funcnames = []
        if self._ctx:
            func = self._ctx.get(option, {}).get('func')
            if func:
                for f in func:
                    funcnames.append(self._ctx_to_funcname_map(f))
        return funcnames

    def _get_func(self, option):
        funcnames = self._get_funcname(option)
        return [getattr(self, fn) for fn in funcnames]

    def _ctx_to_funcname_map(self, name):
        return name

    def _format_value(self, option, values, func):
        value = self._get_value(values)
        if value is _UNSET:
            raise NoOptionError(option, self.name)
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


class OptionParser(object):
    """Parse option values for ``ConfigFetch``."""

    HELP_PREFIX = ':'
    ARGS_PREFIX = '::'
    ARGS_SHORTNAMES = {'f': 'func'}

    def __init__(self, config, ctx):
        self._config = config
        self._ctx = ctx

        # Note: require a space (' ') for nonblank values
        comp = re.compile
        self._help_re = comp(r'^\s*(%s)(?: (.+))*$' % self.HELP_PREFIX)
        self._args_re = comp(r'^\s*(%s)(?: (.+))*\s*$' % self.ARGS_PREFIX)

    def parse(self):
        for secname, section in self._config.items():
            for option in section:
                self._parse_option(section, option)
        return self._ctx

    def _parse_option(self, section, option):
        value = section[option]
        args, value = self._parse_args(value)

        section[option] = value
        if args['argparse']:
            if not self._ctx.get(option):
                self._ctx[option] = {}
            self._ctx[option]['argparse'] = args['argparse']
        if args['func']:
            if not self._ctx.get(option):
                self._ctx[option] = {}
            self._ctx[option]['func'] = args['func']

    def _parse_args(self, value):
        help_ = []
        args = {'argparse': {}, 'func': {}}
        option_value = []
        state = 'root'  # root -> (help) -> (argparse) -> (func) -> value
        error_fmt = 'Invalid line at: %r'

        for line in value.split('\n'):
            if line.strip() == '' and state not in ('help', 'value'):
                continue

            m = self._help_re.match(line)
            if m:
                if state not in ('root', 'help'):
                    raise OptionParseError(error_fmt % line)
                state = 'help'
                help_.append(m.group(2) if m.group(2) else '')
                continue

            m = self._args_re.match(line)
            if m:
                if not m.group(2):
                    raise OptionParseError(error_fmt % line)

                key, val = m.group(2).split(':', maxsplit=1)
                key, val = self._convert_arg(key, val)
                if key != 'func':
                    if state not in ('help', 'argparse'):
                        raise OptionParseError(error_fmt % line)
                    args['argparse'][key] = val
                    state = 'argparse'
                else:
                    if state not in ('root', 'help', 'argparse'):
                        raise OptionParseError(error_fmt % line)
                    args['func'] = val
                    state = 'func'
                continue

            state = 'value'
            option_value.append(line.strip())

        option_value = '\n'.join(option_value)
        if help_:
            args['argparse']['help'] = '\n'.join(help_)
        self._set_argparse_suppress(args)
        return args, option_value

    def _convert_arg(self, key, val):
        key, val = key.strip(), val.strip()
        if key in self.ARGS_SHORTNAMES:
            key = self.ARGS_SHORTNAMES[key]
        return key, self._convert_arg_value(key, val)

    def _convert_arg_value(self, key, val):
        arg_type = {
            'names': 'comma',
            'action': '',
            'nargs': 'number',
            'const': 'number, bool',
            'default': 'number, bool',
            'type': 'eval',
            'choices': 'comma, number',
            'required': 'bool',
            'help': '',
            'metavar': '',
            'dest': '',
            'func': 'comma',
        }
        for conv in arg_type[key].split(','):
            conv = conv.strip()
            if not conv:
                continue
            if conv == 'comma':
                val = _parse_comma(val)
            if conv == 'number':
                val = self._number_or_string(val)
            if conv == 'bool':
                val = self._bool_or_string(val)
            if conv == 'eval':
                val = eval(val)
        return val

    def _number_or_string(self, string):
        # 'string' may be string or a list of string
        if isinstance(string, list):
            return [self._number_or_string(s) for s in string]

        try:
            return int(string)
        except ValueError:
            try:
                return float(string)
            except ValueError:
                m = _STRING_RE.match(string)
                if m:
                    return m.group(2)
                return string

    def _bool_or_string(self, something):
        # something may be string, int or float (or other)
        if something == 'True':
            return True
        if something == 'False':
            return False
        return something

    def _set_argparse_suppress(self, args):
        for key, val in args['argparse'].items():
            if val == 'argparse.SUPPRESS':
                args['argparse'][key] = argparse.SUPPRESS

    def build(self, argument_parser, sections=None):
        if sections is None:
            sections = self._config.sections()
        if isinstance(sections, str):
            sections = [sections]
        for section in sections:
            for option in self._config.options(section):
                self._build(argument_parser, section, option)

    def _build(self, parser, section, option):
        args = self._ctx.get(option, {}).get('argparse')
        if not args or not args.get('help'):
            return

        names = args.pop('names', None) or []
        names.append(option)
        names = self._build_argument_names(names)

        func = self._ctx.get(option, {}).get('func')
        if func and 'bool' in func:
            const = 'no' if args.get('dest') else 'yes'
            bool_arg = {
                'action': 'store_const',
                'const': const,
            }
            args.update(bool_arg)
        parser.add_argument(*names, **args)

    def _build_argument_names(self, names_):
        names = []
        for n in names_:
            if len(n) == 1:
                names.append('-' + n)
                continue
            # permissive rule, both 'v' and '-v' are OK.
            if len(n) == 2 and n[0] == '-':
                names.append(n)
                continue
            names.append('--' + n.replace('_', '-'))
        return names


class ConfigFetch(object):
    """A custom Configuration object.

    It keeps a ``ConfigParser`` object (``_config``)
    and a correspondent option-name-to-metadata map (``_ctx``).

    The metadata includes function list specific to the option name (global).
    Option access returns a functions-applied-value.

    It also has ``argparse.Namespace`` object (``args``),
    and Environment variable dictionay (``envs``).

    They are also global, having no concept of sections.
    If the option name counterpart is defined,
    their value precedes the config value.

    Functions are similarly applied.

    The class ``__init__`` should accept
    all ``ConfigParser.__init__`` keyword arguments.

    The class specific argumants are:

    :param fmts: dictionay ``Func._fmt`` uses
    :param args: ``argparse.Namespace`` object,
        already commandline arguments parsed
    :param envs: dictionary with option name and Environment Variable name
        as key and value
    :param Func: ``Func`` or subclasses, keep actual functions
    :param optionparser: ``OptionParser`` or a subclass,
        parse option value string and build actual value and metadata
    :param parser: ``ConfigParser`` or a subclass,
        keep actual config data
    """

    def __init__(self, *, fmts=None, args=None, envs=None,
            Func=Func, optionparser=OptionParser,
            parser=configparser.ConfigParser, **kwargs):
        self._fmts = fmts or {}
        self._args = args or argparse.Namespace()
        self._envs = envs or {}
        self._Func = Func
        self._optionparser = optionparser
        self._parser = parser
        self._ctx = {}  # option -> metadata dict
        self._cache = {}  # SectionProxy object cache

        self._optionxform = self._get_optionxform()
        self._config = parser(**kwargs)
        self._config.optionxform = self._optionxform

    def read_file(self, f, format=None):
        """Read config from an opened file object.

        :param f: a file object
        :param format: 'fini', 'ini' or ``None``

        If ``format`` is 'fini',
        read config values and metadata.
        Previous metadata definitions are overwritten, if any.

        If ``format`` is 'ini' (or actually any other string than 'fini'),
        read only config values, just using the ``ConfigParser`` or a subclass.
        Metadata are kept intact, if any.

        If ``format`` is ``None`` (default),
        only when the metadata dict (``_ctxs``) is blank,
        read the file as 'fini'
        (supposed to be the first time read).
        Otherwise read the file as 'ini'.
        """
        self._config.read_file(f)
        self._check_and_parse_config(format)

    def read_string(self, string, format=None):
        """Read config from a string.

        :param string: a string
        :param format: 'fini', 'ini' or ``None``

        The meaning of ``format`` is the same as ``.read_file``.
        """
        self._config.read_string(string)
        self._check_and_parse_config(format)

    def _get_optionxform(self):
        def _xform(option):
            return option
        return _xform

    def _check_and_parse_config(self, format):
        if format is None:
            if len(self._ctx) == 0:
                format = 'fini'
        if format == 'fini':
            optionparser = self._optionparser(self._config, self._ctx)
            self._ctx = optionparser.parse()

    def set_arguments(self, argument_parser, sections=None):
        """Run ``argument_parser.add_argument`` according to config metadata.

        :param argument_parser: ``argparse.ArgumentParser`` or a subclass,
            either blank or with some arguments already defined
        :param sections: a section name (string) or section list
            to filter sections, default (``None``) is for all sections

        :returns: argument_parser

        The usage is a bit complex, though. Normally:

        1. Instantiate ``ConfigFetch`` with blank ``arg``.
        2. Create ``ArgumentParser``, edit as necessary.
        3. ``.set_arguments`` (populate ``ArgumentParser`` with metadata).
        4. Parse commandline (``ArgumentParser.parse_args``).
        5. ``.set_args`` below with the new ``args``.
        """
        optionparser = self._optionparser(self._config, self._ctx)
        optionparser.build(argument_parser, sections)
        return argument_parser

    def set_args(self, namespace):
        """Set ``_args`` attribute.

        :param namespace: ``argparse.Namespace`` object

        It manually sets ``_args`` again, after initialization.
        """
        self._args = namespace

    # TODO: Invalidate attribute names this class uses.
    # cf. set(dir(configfetch.fetch(''))) - set(dir(object()))
    def __getattr__(self, section):
        if section in self._cache:
            return self._cache[section]

        s = SectionProxy(
            self, section, self._ctx, self._fmts, self._Func)
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


class SectionProxy(object):
    """``ConfigFetch`` section proxy object.

    Similar to ``ConfigParser``'s proxy object.
    """

    def __init__(self, conf, section, ctx, fmts, Func):
        self._conf = conf
        self._config = conf._config
        self.name = section
        self._ctx = ctx
        self._fmts = fmts
        self._Func = Func

        # 'ConfigParser.__contains__()' includes default section.
        if self._get_section() not in self._config:
            raise NoSectionError(self._get_section())

    # Introduce small indirection,
    # in case it needs special section manipulation in user subclasses.
    def _get_section(self, option=None):
        return self.name

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
        f = self._get_func_class()
        return f(option, values)

    def _get_funcname(self, option):
        f = self._get_func_class()
        optionxform = self._conf._optionxform
        return f._get_funcname(optionxform(option))

    def _get_func_class(self):
        return self._Func(self.name, self._ctx, self._fmts)

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
        return self._config[self.name].__iter__()


class Double(object):
    """Supply a parent section to fallback, before 'DEFAULT'.

    An accessory helper class,
    not so related to this module's main concern.

    Default section is a useful feature of ``INI`` format,
    but it is always global and unconditional.
    Sometimes more fine-tuned one is needed.

    :param sec: ``SectionProxy`` object
    :param parent_sec: ``SectionProxy`` object to fallback
    """

    def __init__(self, sec, parent_sec):
        self.sec = sec
        self.parent_sec = parent_sec

    def __getattr__(self, option):
        funcnames = self.sec._get_funcname(option)
        if funcnames == ['plus']:
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
            return self.parent_sec.get(option)

        if val in (None, '', []):
            try:
                return self.parent_sec.get(option)
            except NoOptionError:
                pass

        return val

    def _get_plus_value(self, option):
        parent_val = self.parent_sec._get_conf(option)
        values = self.sec._get_values(option)
        values = values + [parent_val]
        self._check_unset(values, option, self.sec.name)
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


def fetch(file_or_string, *, encoding=None,
        fmts=None, args=None, envs=None, Func=Func,
        parser=configparser.ConfigParser, **kwargs):
    """Fetch ``ConfigFetch`` object.

    It is a convenience function for the basic use of the library.
    Most arguments are the same as ``ConfigFetch.__init__``.

    the specific arguments are:

    :param file_or_string: a filename to open
        if the name is in system path, or a string
    :param encoding: encoding to use when openning the name

    Files are read with ``format=None``.
    """
    conf = ConfigFetch(fmts=fmts, args=args, envs=envs, Func=Func,
        parser=parser)

    if os.path.isfile(file_or_string):
        with open(file_or_string, encoding=encoding) as f:
            conf.read_file(f)
    else:
        conf.read_string(file_or_string)
    return conf


def _get_plusminus_values(adjusts, initial=None):
    """Add or sbtract values partially (used by ``_plus()``).

    Use ``+`` and ``-`` as the markers.

    :param adjusts: lists of values to process in order
    :param initial: initial values (list) to add or subtract further
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
    """Edit ``option_arguments`` with leading dashes.

    An accessory helper function.
    It unites two arguments to one, if the second argument starts with ``'-'``.

    The reason is that ``argparse`` cannot parse this particular pattern.

    | https://bugs.python.org/issue9334
    | https://stackoverflow.com/a/21894384

    And ``_plus`` uses this type of arguments frequently.

    :param parser: ArgumentParser object,
        already actions registered
    :param matcher: regex string to match options,
        to narrow the targets
        (``None`` means to process all arguments)
    :param args: arguments list to parse, defaults to ``sys.argv[1:]``
        (the same as ``argparse`` default)
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
