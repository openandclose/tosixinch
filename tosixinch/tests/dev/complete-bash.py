#!/usr/bin/env python

"""Generate bash completion file for the application.

Read template and write to a file.
(``complete.template.bash`` and ``tosixinch-complete.bash``, respectively.)

You have to manually pick options for FILE_COMP and DIR_COMP.
"""

import argparse
import os
import sys

import tosixinch.main
import tosixinch.templite


SCRIPT_DIR = os.path.dirname(__file__)
TEMPLATE_FILE = SCRIPT_DIR + '/complete.template.bash'
OUTPUT_FILE = SCRIPT_DIR + '/../../script/tosixinch-complete.bash'


FILE_COMP = {
    '-i', '--input',
    '-f', '--file',
}

DIR_COMP = {
    '--userdir',
}


parser = tosixinch.main._build_parser()

_opt = lambda x: x.option_strings
_cls = lambda x: repr(x.__class__).split('.')[1].split("'")[0]
_type = lambda x: x.type
_choice = lambda x: x.choices


class Namespace(object):
    """Make data object with dot-lookup."""

    pass


def list_options():
    parser._actions.sort(key=lambda x: repr(x.__class__))
    for a in parser._actions:
        list_option(a)


def list_option(action):
    print('%-25s    %-20s type:%-10s choices:%s'
        % (_opt(action), _cls(action), _type(action), _choice(action)))


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
        all_opts.extend(_get_longopt(_opt(a)))

        if _choice(a):
            c = Namespace()
            c.opt = '|'.join(_opt(a))
            c.choices = ' '.join(_choice(a))
            c.name = sorted(_opt(a))[0]  # long options should come in front
            choices.append(c)

        elif _need_args(a):
            # list_option(a)
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
    nargs_actions = (argparse._StoreAction, argparse._AppendAction)
    return isinstance(obj, nargs_actions)


def render(template_file, output):
    context = get_context()
    with open(template_file) as f:
        template = f.read()

    t = tosixinch.templite.Templite(template)
    text = t.render(context)
    # print(text)
    with open(output, 'w') as f:
        f.write(text)


HELP = """python complete-bash.py [-l][-p][-x TEMPLATE_FILE OUTPUT_FILE][-X]
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
