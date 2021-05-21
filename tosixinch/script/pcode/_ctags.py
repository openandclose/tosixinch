
"""Tag pdf bookmark candidates using (Universal or Exuberant) Ctags.

Only called from _pcode.py.
"""

import logging
import os
import shlex
import sqlite3
import subprocess
import sys
import zlib

logger = logging.getLogger(__name__)


class Tags(object):
    """Interface to use the generated ctags file."""

    def __init__(self, tagfile=None, text=None, c2ftype=None):
        self.tagfile = tagfile
        self.text = text or self._read_tag()
        self.c2ftype = c2ftype or {}
        self._files_cache = []
        self.data = list(self._parse_text())
        self.cur = self._create_db()

    def _read_tag(self):
        with open(self.tagfile) as f:
            return f.read()

    def _parse_text(self):
        for ln in self.text.split('\n'):
            if ln:
                if ln.startswith('!_TAG_'):
                    continue
                yield self._parse_line(ln)

    def _parse_line(self, line):
        tag, fname, lnum, *ext = line.split('\t')
        ext = [ext] if isinstance(ext, str) else ext
        try:
            index = self._files_cache.index(fname)
        except ValueError:
            self._files_cache.append(fname)
            index = self._files_cache.index(fname)
        if lnum.endswith(';"'):
            lnum = int(lnum[:-2])
            return (tag, index, lnum, *self._parse_extension(ext))
        return (tag, fname, lnum, '', '', '', '')

    def _parse_extension(self, ext):
        lang = ''
        kind = ''
        fscope = 0
        others = []
        for x in ext:
            if x.startswith('language:'):
                lang = x[9:].lower()
                lang = self.c2ftype.get(lang) or lang
            elif x == 'file:':
                fscope = 1
            elif x == 'kind:':
                kind = x  # memo: there are long and short names.
            elif ':' not in x:
                kind = x
            else:
                others.append(x)
        return lang, kind, fscope, '\t'.join(others)

    def _create_db(self):
        con = sqlite3.connect(':memory:')
        cur = con.cursor()
        cmd = """
            CREATE TABLE tags (
                tag TEXT,
                fname INTEGER,
                lnum INTEGER,
                lang TEXT,
                kind TEXT,
                fscope INTEGER,
                others TEXT
            ) """
        cur.execute(cmd)
        cmd = 'INSERT INTO tags VALUES (?, ?, ?, ?, ?, ?, ?)'
        cur.executemany(cmd, self.data)
        con.commit()
        return cur

    def close_db(self):
        self.cur.connection.close()

    def find(self, tag, ftype, fname):
        if fname not in self._files_cache:
            return [], []

        rows1, rows2 = [], []  # rows1: in the same file, rows2: in other.
        cur = self.cur
        cmd = 'SELECT rowid, * FROM tags WHERE tag = (?) AND lang = (?)'
        cur.execute(cmd, (tag, ftype))
        for row in cur.fetchall():
            if row[2] == self._files_cache.index(fname):
                rows1.append(self._build_row(row))
            else:
                rows2.append(self._build_row(row))
        return rows1, rows2

    def _build_row(self, row):
        # Change filename index row[1] to actual filename.
        return (*row[0:2], self._files_cache[row[2]], *row[3:])


def _create_ctags(tagfile, cmd, files):
    checksumf = tagfile + '.checksum'
    csum = _get_checksum(cmd, files)
    if os.path.isfile(checksumf):
        with open(checksumf) as f:
            if f.read().strip() == csum:
                return
    with open(checksumf, 'w') as f:
        f.write(csum)

    logger.debug('[ctags] creating tags...')
    cmd = shlex.split(cmd, comments='#')
    cmd.extend(('-f', tagfile))
    cmd.extend(files)
    ret = subprocess.run(cmd, capture_output=True)
    args = ret.args
    args = args if isinstance(args, str) else ' '.join(args)
    logger.debug('arguments: %s' % args)
    logger.debug('ctags stdout: %s' % ret.stdout.decode(sys.stdout.encoding))
    logger.debug('ctags stderr: %s' % ret.stderr.decode(sys.stderr.encoding))


def _get_checksum(cmd, files):
    mtime = max(os.stat(f).st_mtime for f in files)
    data = '\n'.join([cmd] + sorted(files) + [str(mtime)])
    data = data.encode('utf-8')
    return '%08x' % (zlib.crc32(data) & 0xffffffff)
