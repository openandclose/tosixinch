
"""Create actual language mapping dictionaries."""

from tosixinch.script.pcode import _ftype_base


def _delete(dicts, values):
    for value in values:
        for dict_ in dicts:
            del_keys = []
            for k, v in dict_.items():
                if v == value:
                    del_keys.append(k)
            for del_key in del_keys:
                del dict_[del_key]


class FType(object):
    """Get ftype base dictionaries and modifies them."""

    DELETES = [
        'html',
    ]

    def __init__(self, path='ctags'):
        self.path = path
        self.p2ftype, self.c2ftype = _ftype_base.get_maps(path)
        self._delete()

    def _delete(self):
        _delete((self.p2ftype, self.c2ftype), self.DELETES)

    def __call__(self):
        p2f, c2f = self.p2ftype, self.c2ftype

        # p2f['reStructuredText'] = 'prose'
        # p2f['markdown'] = 'prose'

        # p2f['Cython'] = 'python'
        # p2f['Numpy'] = 'python'
        # p2f['Python 2.x'] = 'python'

        return p2f, c2f


if __name__ == '__main__':
    import pprint
    pprint.pprint(FType()())
