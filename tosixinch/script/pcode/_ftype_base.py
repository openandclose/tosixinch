#!/usr/bin/env python

"""Create base langauge data from Pygments and Ctags.

Only called form _ftype.py.
"""

import argparse
import subprocess
import sys

import pygments.lexers

HEADING = """
# Compare Pygments and Ctags languages.
# If both names are common, the third colum is added.
# If Pygments' 'aliase' is common, the fourth columns is added.

Pygments(%s)\tCtags(%s)\tCommon names(%s)\tAlternative Pygments name\
\tCommon filenames\tPygments only filenames\tCtags only filenames
""".strip()


def _get_pygments_langs():
    langs = []
    for lexer in pygments.lexers.get_all_lexers():
        name, aliases, filenames, mimetypes = lexer
        langs.append([name.lower(), name, aliases, filenames])
    return sorted(langs)


def _get_ctags_langs(path):
    langs = []
    ret = subprocess.run([path, '--list-maps'], capture_output=True)
    maps = ret.stdout.decode(sys.stdout.encoding).split('\n')[:-1]
    for map_ in maps:
        k, *v = map_.split()
        langs.append([k.lower(), k, '', v])

    return sorted(langs)


def _next(x):
    try:
        return next(x)
    except StopIteration:
        return ['zzzz', '', '', '']  # always greater than other names


def _check_pygments_aliases(plangs, cname):
    for plang in plangs:
        name, pname, aliases, *rest = plang
        if cname.lower() in aliases:
            return plang
    return False


def _paren(x):
    return '(%s)' % x


def _unparen(x):
    if x.startswith('(') and x.endswith(')'):
        return x[1:-1]
    return x


def _build_diff(plangs, clangs):
    # make four element list, the third is non-blank, if common.
    # If Pygments's aliase is common, the fourth is 'that' Pygments's name.
    plangs = plangs
    clangs = iter(clangs)
    out = []
    c = _next(clangs)
    for p in plangs:
        while p[0] > c[0]:
            another_p = _check_pygments_aliases(plangs, c[0])
            if another_p:
                out.append(['', c, _paren(c[0]), another_p])
            else:
                out.append(['', c, '', ''])
            c = _next(clangs)

        if p[0] == c[0]:
            out.append([p, c, c[0], ''])
            c = _next(clangs)
        elif p[0] < c[0]:
            out.append([p, '', '', ''])
    return out


def _get_diff_sets(x, y):
    tostirng = lambda a: ' '.join(sorted(list(a)))
    x, y = set(x), set(y)
    comm = x & y
    return tostirng(comm), tostirng(x - comm), tostirng(y - comm)


def _add_filenames(out_):
    out = []
    for o in out_:
        p, c, common, another_p = o
        pnames = p and p[3] or []
        if another_p:
            pnames += another_p[3]
        cnames = c and c[3] or []
        out.append([p, c, common, another_p, *_get_diff_sets(pnames, cnames)])
    return out


def print_names(plangs, clangs, out):
    """Print tab separated csv text."""
    nums = [len(plangs), len(clangs)]
    cnt = 0
    for o in out:
        p, c, common, *rest = o
        if common:
            cnt += 1
    nums.append(cnt)

    p, c, common = nums
    print(HEADING % (p, c, common))

    for o in out:
        p, c, common, another_p, *rest = o
        p = p and p[1] or ''
        c = c and c[1] or ''
        another_p = another_p and _paren(another_p[1]) or ''
        print('\t'.join((p, c, common, another_p, *rest)))


def _build_dict(out):
    dict_ = {}
    P = 'pygments'
    C = 'ctags'

    for o in out:
        p, c, common, another_p, *rest = o
        p = p and p[1] or ''
        c = c and c[1] or ''
        another_p = another_p and another_p[1] or ''
        if common:
            dict_[_unparen(common)] = {P: [p or another_p], C: [c]}
    return dict_


def print_dict(dict_):
    """Print pretty-printed FTYPE dictionary."""
    print('FTYPE = {')
    fmt = """\
    %r: {
        'pygments': %r,
        'ctags': %r,
    },"""
    for k, v in dict_.items():
        v1 = v['pygments']
        v2 = v['ctags']
        print(fmt % (k, v1, v2))
    print('}')


def _get_data(path):
    plangs = _get_pygments_langs()
    clangs = _get_ctags_langs(path)

    out = _build_diff(plangs, clangs)

    return plangs, clangs, out


def get_maps(path='ctags'):
    plangs, clangs, out = _get_data(path)
    p2ftype = {}  # Pygments to ftype
    c2ftype = {}  # Ctags to ftype
    for o in out:
        p, c, common, another_p, *rest = o
        p = p and p[1] or ''
        c = c and c[1] or ''
        another_p = another_p and another_p[1] or ''
        if common:
            p2ftype[p or another_p] = _unparen(common)
            c2ftype[c] = _unparen(common)
    return c2ftype, p2ftype


def _parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-p', '--path', default='ctags',
        help="path for Ctags, default: 'ctags'.")

    parser.add_argument('-n', '--names',
        action='store_const', const='yes',
        help='print tab separated language names list (csv)')

    parser.add_argument('-d', '--dict',
        action='store_const', const='yes',
        help='print base ftype dictionary')

    args = parser.parse_args()
    return parser, args


def main():
    parser, args = _parse_args()

    plangs, clangs, out = _get_data(args.path)

    if args.names:
        out = _add_filenames(out)
        print_names(plangs, clangs, out)
        return

    if args.dict:
        dict_ = _build_dict(out)
        print_dict(dict_)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
