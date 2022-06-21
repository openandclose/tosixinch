
import os
import sys

from tosixinch import action

TESTDIR = os.path.dirname(__file__)
ROOTDIR = os.path.join(TESTDIR, 'res', 'filename')

os.chdir(ROOTDIR)


def test_read():
    text = action.read('aaa/aa')
    assert text.strip() == 'aaa/aa'

    text = action.read('bbb/bb')
    assert text.strip() == 'bbb/bb.f'

    text = action.read('ccc/cc')
    assert text.strip() == 'ccc/cc.orig'

    text = action.read('ddd/dd')
    assert text.strip() == 'ddd/dd.orig'


def test__set_dfile():
    def set(efile):
        return action._File()._set_dfile(efile)

    assert set('aaa/aa') == ('aaa/aa', 'aaa/aa.orig')
    assert set('bbb/bb') == ('bbb/bb.f', 'bbb/bb.orig')
    assert set('ccc/cc') is None
    assert set('ddd/dd') is None


def test__set_finlename():
    def get(fname):
        files = action._File()._set_filename(fname)
        return [os.path.relpath(fn) for fn in files]

    assert get('aaa/aa') == ['aaa/aa']
    assert get('bbb/bb') == []
    assert get('ccc/cc') == ['ccc/cc']
    assert get('ddd/dd') == []
