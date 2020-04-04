#!/usr/bin/env python

"""Generate bash completion file for the application.

Read template and write to a file.
(``_tosixinch.t.bash`` and ``_tosixinch.bash``, respectively.)

You have to manually pick options for FILE_COMP and DIR_COMP.
"""

import argparse
import os
import sys

import tosixinch.main
import tosixinch.templite


SCRIPT_DIR = os.path.dirname(__file__)
TEMPLATE_FILE = SCRIPT_DIR + '/_tosixinch.t.bash'
OUTPUT_FILE = SCRIPT_DIR + '/../../data/_tosixinch.bash'


FILE_COMP = {
    '-f', '--file',
    '-i', '--input',
    '--cnvpath',
}

DIR_COMP = {
    '--userdir',
}

# Python 3.7.4
CODECS = """
    ascii big5 big5hkscs cp037 cp1006 cp1026 cp1125 cp1140 cp1250 cp1251
    cp1252 cp1253 cp1254 cp1255 cp1256 cp1257 cp1258 cp273 cp424 cp437 cp500
    cp65001 cp720 cp737 cp775 cp850 cp852 cp855 cp856 cp857 cp858 cp860 cp861
    cp862 cp863 cp864 cp865 cp866 cp869 cp874 cp875 cp932 cp949 cp950
    euc-jis-2004 euc-jisx0213 euc-jp euc-kr gb18030 gb2312 gbk hz iso2022-jp
    iso2022-jp-1 iso2022-jp-2 iso2022-jp-2004 iso2022-jp-3 iso2022-jp-ext
    iso2022-kr iso8859-10 iso8859-11 iso8859-13 iso8859-14 iso8859-15
    iso8859-16 iso8859-2 iso8859-3 iso8859-4 iso8859-5 iso8859-6 iso8859-7
    iso8859-8 iso8859-9 johab koi8-r koi8-t koi8-u kz1048 latin-1
    mac-cyrillic mac-greek mac-iceland mac-latin2 mac-roman mac-turkish
    ptcp154 shift-jis shift-jis-2004 shift-jisx0213 utf-16 utf-16-be utf-16-le
    utf-32 utf-32-be utf-32-le utf-7 utf-8 utf-8-sig mbcs oem
""".strip().split()

OPTIONAL_CHOICES = {
    '--encoding': sorted(CODECS),
}


_, parser = tosixinch.main._get_parser()

_opt = lambda x: x.option_strings
_cls = lambda x: repr(x.__class__).split('.')[1].split("'")[0]
_type = lambda x: x.type
_choice = lambda x: x.choices
_nargs = lambda x: x.nargs

_opt_choice = lambda x: OPTIONAL_CHOICES.get(_get_longopt(_opt(x))[0])


class Namespace(object):
    """Make data object with dot-lookup."""


def list_options():
    parser._actions.sort(key=lambda x: repr(x.__class__))
    for a in parser._actions:
        list_option(a)


def list_option(action):
    print('%-25s    %-20s nargs:%-10s type:%-10s choices:%s'
        % (_opt(action), _cls(action),
            _nargs(action), _type(action), _choice(action)))


def short_printout(sep=' '):
    out = []
    for a in parser._actions:
        out.extend(_opt(a))
    print(sep.join(out))


def get_context():
    context = {}

    no_comp = []
    choices = []
    all_opts = []
    for a in parser._actions:
        if a.help == '==SUPPRESS==':
            continue
        all_opts.extend(_get_longopt(_opt(a)))

        if _choice(a) or _opt_choice(a):
            c = Namespace()
            c.opt = '|'.join(_opt(a))
            c.choices = ' '.join(_choice(a) or _opt_choice(a))
            c.name = sorted(_opt(a))[0]  # long options should come in front
            choices.append(c)

        elif _need_args(a):
            o = set(_opt(a))
            if o.isdisjoint(FILE_COMP | DIR_COMP):
                no_comp.extend(o)

    context['no_comp'] = '|'.join(sorted(no_comp))
    context['choices'] = sorted(choices, key=lambda x: x.name)
    context['file_comp'] = '|'.join(sorted(list(FILE_COMP)))
    context['dir_comp'] = '|'.join(sorted(list(DIR_COMP)))
    context['all_opts'] = ' '.join(sorted(all_opts))

    return context


def _get_longopt(opt):
    return [o for o in opt if o.startswith('--')]


def _need_args(obj):
    return obj.nargs != 0


def render(template_file, output):
    context = get_context()
    with open(template_file) as f:
        template = f.read()

    t = tosixinch.templite.Templite(template)
    text = t.render(context)
    # print(text)
    with open(output, 'w') as f:
        f.write(text)


HELP = """python argparse2bash.py [-l][-p][-x TEMPLATE_FILE OUTPUT_FILE][-X]
    -l: list detailed options data to look and see.
    -p: print out just option names (may be good for copy and paste).
    -x: actually render TEMPLATE_FILE, write to OUTPUT_FILE
    -X: render with predetermined files (main use).
"""


def usage():
    print(HELP)
    sys.exit()


if __name__ == '__main__':
    args = sys.argv[1:]
    if '-l' in args:
        list_options()
    elif '-p' in args:
        short_printout()
    elif '-x' in args:
        args.pop(args.index('-x'))
        try:
            render(args[0], args[1])
        except IndexError:
            usage()
    elif '-X' in args:
        render(TEMPLATE_FILE, OUTPUT_FILE)
    else:
        usage()
