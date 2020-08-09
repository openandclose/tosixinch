
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


class OptionBuildError(Error):
    """Raised when config file has a invalid line."""


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


class DictOptionBuilder(object):
    """Parse and edit option values from a dictionay."""

    def __init__(self, conf):
        self._config = conf._config
        self._conf = conf

    def parse(self, input_):
        if not isinstance(input_, dict):
            raise ValueError('input data must be dict.')

        self._input = input_
        return self._parse()

    def _parse(self):
        ctx = {}
        for sec, section in self._input.items():
            if sec not in self._config:
                self._config.add_section(sec)
            for opt, option in section.items():
                self._parse_option(sec, section, opt, option, ctx)
        return ctx

    def _parse_option(self, sec, section, opt, option, ctx):
        self._config[sec][opt] = option['value']
        if option.get('argparse'):
            if not ctx.get(opt):
                ctx[opt] = {}
            ctx[opt]['argparse'] = option['argparse']
        if option.get('func'):
            if not ctx.get(opt):
                ctx[opt] = {}
            ctx[opt]['func'] = option['func']


class FiniOptionBuilder(object):
    """Parse ``FINI`` option values and create context dict."""

    HELP_PREFIX = ':'
    ARGS_PREFIX = '::'
    ARGS_SHORTNAMES = {'f': 'func'}

    def __init__(self, conf):
        self._config = conf._config
        self._conf = conf

        # Note: require a space (' ') for nonblank values
        comp = re.compile
        self._help_re = comp(r'^\s*(%s)(?: (.+))*$' % self.HELP_PREFIX)
        self._args_re = comp(r'^\s*(%s)(?: (.+))*\s*$' % self.ARGS_PREFIX)

    def parse(self, input_):
        """Parse input and build conifg data and metadata."""
        if hasattr(input_, 'read'):
            self._config.read_file(input_)
        elif isinstance(input_, str):
            self._config.read_string(input_)
        else:
            raise ValueError('input data must be file object or string.')

        self._input = input_
        return self._parse()

    def _parse(self):
        ctx = {}
        for secname, section in self._config.items():
            for option in section:
                self._parse_option(section, option, ctx)
        return ctx

    def _parse_option(self, section, option, ctx):
        value = section[option]
        args, value = self._parse_args(value)

        section[option] = value
        if args['argparse']:
            if not ctx.get(option):
                ctx[option] = {}
            ctx[option]['argparse'] = args['argparse']
        if args['func']:
            if not ctx.get(option):
                ctx[option] = {}
            ctx[option]['func'] = args['func']

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
                    raise OptionBuildError(error_fmt % line)
                state = 'help'
                # create blank 'help' key beforehand, to preserve key order
                args['argparse']['help'] = ''
                help_.append(m.group(2) if m.group(2) else '')
                continue

            m = self._args_re.match(line)
            if m:
                if not m.group(2):
                    raise OptionBuildError(error_fmt % line)

                key, val = m.group(2).split(':', maxsplit=1)
                key, val = self._convert_arg(key, val)
                if key != 'func':
                    if state not in ('help', 'argparse'):
                        raise OptionBuildError(error_fmt % line)
                    args['argparse'][key] = val
                    state = 'argparse'
                else:
                    if state not in ('root', 'help', 'argparse'):
                        raise OptionBuildError(error_fmt % line)
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


class ArgumentBuilder(object):
    """Fill ``argparse.ArgumentParser`` object with arguments."""

    def __init__(self, conf):
        self._config = conf._config
        self._ctx = conf._ctx

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

    It also has ``argparse.Namespace`` object (``args``),
    and Environment variable dictionay (``envs``).

    If the option name counterpart is defined in ``args`` or ``envs``,
    their value precedes the config value.

    So most config option names must be global,
    since ``args`` and ``envs`` do not have ``section`` namespace.

    E.g. if a config has 'foo' section and 'bar' option in it,
    ``args``, and ``envs`` just check the name 'bar',
    ignoring section hierarchy.

    The metadata includes function list specific to the option name.
    Option access gets value from ``arg``, ``envs`` or config,
    and returns a functions-applied-value.

    The class ``__init__`` should accept
    all ``ConfigParser.__init__`` keyword arguments.

    Additional argumants are:

    :param fmts: dictionay ``Func._fmt`` uses
    :param args: ``argparse.Namespace`` object
    :param envs: dictionary with option name and Environment Variable name
        as key and value
    :param Func: ``Func`` or subclasses, worker to keep and look-up functions
    :param option_builder: ``DictOptionBuilder`` or ``FiniOptionBuilder``,
        worker to build value and metadata from data input
    :param parser: ``ConfigParser`` or a subclass,
        keep actual config values
    """

    def __init__(self, *, fmts=None, args=None, envs=None,
            Func=Func, option_builder=DictOptionBuilder,
            parser=configparser.ConfigParser, **kwargs):
        self._fmts = fmts or {}
        self._args = args or argparse.Namespace()
        self._envs = envs or {}
        self._Func = Func
        self._option_builder = option_builder
        self._parser = parser
        self._ctx = {}  # option -> metadata dict
        self._cache = {}  # SectionProxy object cache

        self._optionxform = self._get_optionxform()
        self._config = parser(**kwargs)
        self._config.optionxform = self._optionxform

    def fetch(self, input_):
        """Read input and build config data and metadata.

        Note type of input entirely depends on option_builder.
        ``DictOptionBuilder`` accepts only python dictionary object.
        ``FiniOptionBuilder`` accepts only opened file object or string.
        """
        option_builder = self._option_builder(self)
        self._ctx.update(option_builder.parse(input_))

        # shortcut
        self.read = self._config.read
        self.read_file = self._config.read_file
        self.read_string = self._config.read_string
        self.read_dict = self._config.read_dict

    def _get_optionxform(self):
        def _xform(option):
            return option
        return _xform

    def build_arguments(self, argument_parser, sections=None):
        """Run ``argument_parser.add_argument`` according to config metadata.

        :param argument_parser: ``argparse.ArgumentParser`` or a subclass,
            either blank or with some arguments already defined
        :param sections: a section name (string) or section list
            to filter sections, default (``None``) is for all sections

        :returns: argument_parser

        The usage is a bit complex, though. Normally:

        1. Instantiate ``ConfigFetch`` with blank ``arg``.
        2. Create ``ArgumentParser``, edit as necessary.
        3. ``.build_arguments`` (populate ``ArgumentParser`` with arguments).
        4. Parse commandline (``ArgumentParser.parse_args``).
        5. ``.set_arguments`` below with the new ``args``.
        """
        ArgumentBuilder(self).build(argument_parser, sections)
        return argument_parser

    def set_arguments(self, namespace):
        """Set ``_args`` attribute.

        :param namespace: ``argparse.Namespace`` object

        It manually sets ``_args`` again, after initialization.
        """
        self._args = namespace

    # TODO: Invalidate attribute names this class uses.
    # cf. set(dir(configfetch.fetch(''))) - set(dir(object()))
    def __getattr__(self, section):
        if section not in self._cache:
            s = SectionProxy(
                self, section, self._ctx, self._fmts, self._Func)
            self._cache[section] = s
        return self._cache[section]

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
    """Supply a parent section fallback, before 'DEFAULT'.

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


def fetch(input_, *, encoding=None,
        fmts=None, args=None, envs=None, Func=Func,
        parser=configparser.ConfigParser, option_builder=DictOptionBuilder,
        **kwargs):
    """Fetch ``ConfigFetch`` object.

    It is a convenience function for the basic use of the library.
    Most arguments are the same as ``ConfigFetch.__init__``.

    the specific arguments are:

    :param input_: ``dict``, ``file obj`` or ``string``
        according to ``option_builder``.
        Additionally, if the input is string and in system path,
        it tries to open to make file object
    :param encoding: encoding to use when opening the input
    """
    conf = ConfigFetch(fmts=fmts, args=args, envs=envs, Func=Func,
        parser=parser, option_builder=option_builder)

    if issubclass(option_builder, FiniOptionBuilder):
        if isinstance(input_, str) and os.path.isfile(input_):
            with open(input_, encoding=encoding) as f:
                conf.fetch(f)
                return conf

    conf.fetch(input_)
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


class ConfigPrinter(object):
    """Print dictionay or INI format strings from configuration.

    :param conf: ConfigFetch object, with _config and _ctx attributes
    :param sections: list of section names to print, all sections if None
    :param width: indent unit width
    :param print: any function with one string argument,
        to customize printout behavior
    """

    def __init__(self, conf, sections=None, width=4, print=print):
        self._conf = conf
        self.sections = sections
        self._dict = self.build_dict(conf)
        self.width = width
        self.print = print

    # Build clean dictionay from conf object
    def build_dict(self, conf):

        def build_section(section, ctx, defaults=None):
            d = {}
            for option, value in section.items():
                if value is None:
                    continue
                if defaults and option in defaults:
                    if value == defaults[option]:
                        continue
                d[option] = build_option(option, value, ctx)
            return d

        def build_option(option, value, ctx):
            d = {}
            for key in ctx:
                if key == option:
                    for k, v in ctx[key].items():
                        d[k] = v
            if value is not None:
                d['value'] = value
            return d

        config = conf._config
        ctx = conf._ctx

        default_section = config.default_section
        defaults = config.defaults()
        section_names = self.sections or config.sections()

        d = {}
        section = build_section(defaults, ctx)
        if section:
            d[default_section] = section

        for sec in section_names:
            section = config[sec]
            if len(section) == 0:
                continue
            section = build_section(section, ctx, defaults)
            if section:
                d[sec] = section

        return d

    def print_dict(self):
        """Print dictionary string."""
        width = self.width
        print = self.print

        def iterate(d, level):

            def p(string):
                s = ' ' * level * width + string
                print(s)

            for k, v in d.items():
                if getattr(v, 'items', None):
                    p('%r: {' % k)
                    iterate(v, level + 1)
                    p('},')
                else:
                    p('%r: %r,' % (k, v))

        print('{')
        iterate(self._dict, level=1)
        print('}')

    def print_ini(self):
        """Print INI format string."""
        width = self.width
        print = self.print

        def p(string):
            print(string.rstrip())

        option_len = 0
        for sec, section in self._dict.items():
            for option, value in section.items():
                if len(option) > option_len:
                    option_len = len(option)

        # Just avoiding importing math module
        # https://stackoverflow.com/a/14822457
        # plus 1 for '='
        ceil = (option_len + 1 + width - 1) // width
        option_len = ceil * width

        for sec, section in self._dict.items():
            p('[%s]' % sec)
            for option, val in section.items():
                value = val['value']
                first, *rest = value.split('\n')
                p('%*s%s' % (-option_len, option + '=', first))
                if rest:
                    for r in rest:
                        p('%s%s' % (' ' * option_len, r))
            print('')
