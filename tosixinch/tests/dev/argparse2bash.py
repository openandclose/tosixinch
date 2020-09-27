
"""Generate bash completion string from argparse.ArgumentParser object."""

import os

try:
    from . import templite
except ImportError:
    templite = None

TEMPLATE = 'complete.t.bash'
TEMPLATE = os.path.join(os.path.dirname(__file__), TEMPLATE)


class Namespace(object):
    """Make data object with dot-lookup."""


class Processor(object):
    """Build template context and render template file."""

    def __init__(self, parser, opt_choices=None,
            file_comp=None, dir_comp=None,
            prefix='_', template=TEMPLATE, template_engine=templite):
        self.parser = parser
        self.opt_choices = opt_choices
        self.file_comp = file_comp
        self.dir_comp = dir_comp
        self.prefix = prefix
        self.template = template
        self.template_engine = template_engine

    def _get_context(self):
        context = {}
        no_comp = []
        choices = []
        all_opts = []

        for a in self.parser._actions:
            if a.help == '==SUPPRESS==':
                continue
            all_opts.extend(self._get_longopts(a.option_strings))

            ch = a.choices or self._get_opt_choices(a, self.opt_choices)
            if ch:
                c = Namespace()
                c.opt = '|'.join(a.option_strings)
                c.choices = ' '.join(ch)
                # long options should come in front when sorted
                c.name = sorted(a.option_strings)[0]
                choices.append(c)
            elif a.nargs != 0:
                no_comp.extend(self._get_no_comp_opts(
                    a, self.file_comp, self.dir_comp))

        context['prog'] = self.parser.prog
        context['prefix'] = self.prefix

        context['no_comp'] = '|'.join(sorted(no_comp))
        context['choices'] = sorted(choices, key=lambda x: x.name)
        context['file_comp'] = '|'.join(sorted(list(self.file_comp)))
        context['dir_comp'] = '|'.join(sorted(list(self.dir_comp)))
        context['all_opts'] = ' '.join(sorted(all_opts))

        return context

    def _get_longopts(self, opt):
        return [o for o in opt if o.startswith('--')]

    def _get_opt_choices(self, action, opt_choices):
        return opt_choices.get(self._get_longopts(action.option_strings)[0])

    def _get_no_comp_opts(self, action, file_comp, dir_comp):
        opts = set(action.option_strings)
        file_comp = set(file_comp)
        dir_comp = set(dir_comp)
        return list(opts - (file_comp | dir_comp))

    def render(self):
        context = self._get_context()
        return self._render(context)

    def _render(self, context):
        with open(self.template) as f:
            text = f.read()

        t = self.template_engine.Templite(text)
        return t.render(context)

    def list_options(self, parser):
        actions = self.parser._actions.sorted(key=lambda x: repr(x.__class__))
        for a in actions:
            _cls = repr(a.__class__).split('.')[1].split("'")[0]
            fmt = '%-30s    %-20s nargs:%-10s type:%-10s choices:%s'
            print(fmt % (a.option_strings, _cls, a.nargs, a.type, a.choices))


def render(parser, opt_choices=None,
        file_comp=None, dir_comp=None,
        prefix='_', template=TEMPLATE, template_engine=templite):
    """
    Generate bash completion string from argparse.ArgumentParser object.

    :param parser: argparse.ArgumentParser object to parse
    :param opt_choices: optional choice candidates,
            independent from argparse
    :param file_comp: list of option_strings after which
            file completion is disirable
    :param dir_comp: list of option_strings after which
            directory completion is disirable
    :param prefix: prefix to completion function name for shell,
            default: '_'
    :param template: template for completion
            rendered by a templite library
            default: 'complete.t.bash'
    :param template_engine: templite or similar library
            default: templite

    :return: string

    opt_choices:

    argparse nargs choices are always required to select one of them.
    this opt_choices is only for suggestion,
    users can select other option_argments.
    The format is a dict in which key is the first long option_string,
    and value is a list of choices to complete.

    e.g.
    {'--encoding': ['ascii', 'utf-8', 'latin1'],}


    file_comp, dir_comp:

    You have to manually provide all option_strings (short and long).


    templite:

    A module in Ned Batchelder's Coverage.py.
    https://github.com/nedbat/coveragepy/blob/master/coverage/templite.py

    Included in this library's package.
    """
    processor = Processor(parser, opt_choices,
        file_comp, dir_comp, prefix, template, template_engine)
    return processor.render()
