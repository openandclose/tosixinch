#!/usr/bin/env python

"""Generate INI files from FINI configuration files.

data/fini/_tosixinch.fini   -> data/tosixinch.ini
data/fini/_site.fini        -> data/site.ini
"""

import sys

import tosixinch.configfetch
import tosixinch.main

# Presuppose it is called from repository top directory.
APPFILE = 'tosixinch/data/tosixinch.ini'
SITEFILE = 'tosixinch/data/site.ini'


def _get_conf():
    conf, _ = tosixinch.main._get_parser()
    return conf


def _write_file(fname, ret):
    with open(fname, 'w') as f:
        f.write('\n'.join(ret))


def print_conf(conf, sections=None, filename=None):
    ret = ['']
    if filename:
        p = ret.append
    else:
        p = print

    printer = tosixinch.configfetch.ConfigPrinter
    printer(conf, sections=sections, print=p).print_ini()

    if filename:
        _write_file(filename, ret)


def main(to_file=False):

    conf = _get_conf()

    filename = APPFILE if to_file else None
    print_conf(conf._appconf, filename=filename)

    filename = SITEFILE if to_file else None
    print_conf(conf._siteconf, sections=['scriptdefault'], filename=filename)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        main(to_file=True)
    elif sys.argv[1] in ('p', '-p', '--print'):
        main(to_file=False)
