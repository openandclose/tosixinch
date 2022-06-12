#!/usr/bin/env python

"""Create bash completion file (_tosixinch.bash)."""

import os
import sys

import tosixinch.main
import tosixinch.templite

import argparse2bash

SCRIPT_DIR = os.path.dirname(__file__)
TEMPLATE = os.path.join(SCRIPT_DIR, 'complete.t.bash')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, '../../data/_tosixinch.bash')

FILE_COMP = {
    '-f', '--file',
    '-i', '--input',
    '--cnvpath',
}

DIR_COMP = {
    '--userdir',
}

# CPython 3.10.0 alpha 0
# Procedure:
# run Tools/unicode/listcodecs.py
# remove unsuitable ones (idna, base64_codec etc.)
# add mbcs and oem
CODECS = """
    ascii big5 big5hkscs cp037 cp1006 cp1026 cp1125 cp1140 cp1250 cp1251
    cp1252 cp1253 cp1254 cp1255 cp1256 cp1257 cp1258 cp273 cp424 cp437 cp500
    cp65001 cp720 cp737 cp775 cp850 cp852 cp855 cp856 cp857 cp858 cp860 cp861
    cp862 cp863 cp864 cp865 cp866 cp869 cp874 cp875 cp932 cp949 cp950
    euc-jis-2004 euc-jisx0213 euc-jp euc-kr gb18030 gb2312 gbk hp-roman8 hz
    iso2022-jp iso2022-jp-1 iso2022-jp-2 iso2022-jp-2004 iso2022-jp-3
    iso2022-jp-ext iso2022-kr iso8859-10 iso8859-11 iso8859-13 iso8859-14
    iso8859-15 iso8859-16 iso8859-2 iso8859-3 iso8859-4 iso8859-5 iso8859-6
    iso8859-7 iso8859-8 iso8859-9 johab koi8-r koi8-t koi8-u kz1048 latin-1
    mac-arabic mac-centeuro mac-croatian mac-cyrillic mac-farsi mac-greek
    mac-iceland mac-latin2 mac-roman mac-turkish palmos ptcp154 shift-jis
    shift-jis-2004 shift-jisx0213 tis-620 utf-16 utf-16-be utf-16-le utf-32
    utf-32-be utf-32-le utf-7 utf-8 utf-8-sig mbcs oem
    ftfy html5prescan
""".strip().split()

OPTIONAL_CHOICES = {
    '--encoding': sorted(CODECS),
}


def main():
    _, parser = tosixinch.main._get_parser()
    string = argparse2bash.render(parser, opt_choices=OPTIONAL_CHOICES,
        file_comp=FILE_COMP, dir_comp=DIR_COMP,
        template=TEMPLATE, template_engine=tosixinch.templite)

    with open(OUTPUT_FILE, 'w') as f:
        f.write(string)


if __name__ == '__main__':
    main()
