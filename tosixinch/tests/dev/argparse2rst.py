#!/usr/bin/env python

import re
import sys
import subprocess

import tosixinch.main

# list of returned texts from print_args.
RET = []

# Presuppose it is called from repository top directory.
FL = 'docs/commandline.rst'

MSG = '[auto] update commandline.rst'


def print_args(print=print):
    _, parser = tosixinch.main._get_parser()
    formatter = parser._get_formatter()
    for g in parser._action_groups:
        # if g.title in ('positional arguments', 'optional arguments', 'options'):
        #     continue
        if not g._group_actions:
            continue

        t = g.title.title()
        underline = '-' * len(t)
        print('%s\n%s\n' % (t, underline))

        for a in g._group_actions:
            h = a.help.replace('\n', ' ')
            if h == '==SUPPRESS==':
                continue
            # o = ', '.join(a.option_strings)
            o = formatter._format_action_invocation(a)
            o = _check_too_long_choices(o)
            print('.. option:: %s\n\n    %s\n' %  (o, h))
            d = a.default
            c = a.choices
            if d:
                print('        default=%s\n' % d)
            if c:
                print('        choices=%s\n' % ', '.join(c))


def _check_too_long_choices(s):
    if len(s) < 100:
        return s
    shorter_s = re.sub(r'^(-.+?) {[^{}]+?}$', r'\1 { (choices...) }', s)
    return shorter_s


def edit():
    text = []
    with open(FL) as f:
        for t in f:
            text.append(t)
            if t.strip() == '.. autogenerate':
                break
    text.append('\n')
    text = [''.join(text)]
    text.extend(RET)
    return text


def write_file(text):
    with open(FL, 'w') as f:
        # f.writelines(text)
        f.write('\n'.join(text))


# Presuppose it is called from repository top directory.
def git_commit():
    cmd = ['git', 'add', FL]
    subprocess.run(cmd)
    cmd = ['git', 'commit', FL, '-m', MSG]
    subprocess.run(cmd)


def main():
    print_args(print=RET.append)
    # print('\n'.join(RET))
    text = edit()
    write_file(text)
    git_commit()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        main()
    elif sys.argv[1] in ('p', '-p', '--print'):
        print_args()
