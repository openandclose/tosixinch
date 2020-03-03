
"""Browser to e-reader in a few minutes.

A Python3 script to help to convert html to pdf,
suitable for actual reading in 6-inch e-readers.
"""

# Default logging level for the script is changed to ``info``.
# Logging is used mostly as a feature-rich ``print``.

import logging


def _add_handler(logger, formatter):
    """Add simple passthrough printout handler."""
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def _set_logger(level='info'):
    """Configure logging for application."""
    if level == 'warning':
        num = 30
        fmt = '%(message)s'
    elif level == 'info':
        num = 20
        fmt = '%(message)s'
    elif level == 'debug':
        num = 10
        fmt = '%(name)s:%(levelname)s: %(message)s'

    # root logger
    logger = logging.getLogger()
    if level == 'debug':
        logger.setLevel(num)
    if not logger.hasHandlers():
        formatter = logging.Formatter(fmt)
        _add_handler(logger, formatter)

    # tosixinch logger
    logger = logging.getLogger(__name__)
    logger.setLevel(num)

    del logger


class _ImportError(object):
    """Delay raising ``ImportError`` until first non-special attribute lookup.

    Details like Traceback are not followed.
    """

    def __init__(self, modname):
        self.modname = modname

    def __bool__(self):
        # In case the module is tested like 'if module: ...'
        return False

    def __repr__(self):
        return '<%r will raise ImportError if used.>' % self.modname

    def __getattr__(self, name):
        raise ImportError('%r seems not installed' % self.modname)


# Use bottle.py version.
# See also:
# functools.cached_property (new in Python3.8)
# https://github.com/pydanny/cached-property
# https://github.com/django/django/blob/master/django/utils/functional.py
class cached_property(object):  # noqa N801
    """Delay setting instance attributes.

    A property that is only computed once per instance
    and then replaces itself with an ordinary attribute.
    Deleting the attribute resets the property.
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value
