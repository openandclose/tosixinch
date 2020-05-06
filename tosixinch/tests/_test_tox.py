
"""Check if ``tox`` actually test the virtually installed package.

Instead of my actual installation or files in current directory.
"""

import os
import sys

import pytest  # noqa: F401

import tosixinch.main


def check_installation():
    toxdir = '/.tox/'
    x = toxdir in sys.executable
    y = toxdir in os.path.abspath(tosixinch.__file__)
    return x, y


def test_pytest():
    x, y = check_installation()
    assert x == y


def main():
    x, y = check_installation()
    if x != y:
        msg = ("python and tosixinch should be "
            "either both in the tox environment, or both not.")
        raise EnvironmentError(msg)

    if x:
        try:
            import tosixinch.tests
            msg = "tox environment shouldn't have 'tosixinch.tests'."
            raise EnvironmentError(msg)
        except ImportError:
            pass


if __name__ == '__main__':
    main()
