
import pytest  # noqa: F401

import tosixinch.main


class TestParse:

    def test_add_binary_extension(self):
        base_args = [
            '--input', 'http://example.com', '--add-binary-extensions']

        num = 238  # number of items in the extension list

        args = base_args + ['aaa']
        conf = tosixinch.main._main(args=args)
        assert conf.general.add_binary_extensions == ['aaa']
        
        args = base_args + ['+aaa']
        conf = tosixinch.main._main(args=args)
        assert len(conf.general.add_binary_extensions) == num + 1
        assert conf.general.add_binary_extensions[-1] == 'aaa'

        args = base_args + ['-pdf']
        conf = tosixinch.main._main(args=args)
        assert len(conf.general.add_binary_extensions) == num - 1
        assert 'pdf' not in conf.general.add_binary_extensions
