# ----------------------------------------------------------------------------
# Copyright (c) 2025, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import click
import sys
import json

from q2doc.common import is_book, write_plugin, write_bibtex
from q2doc.cache import get_cache
from q2doc.directives import spec_directives, run_directive
from q2doc.transforms import spec_transforms, run_transform


ROOT_COMMAND_HELP = """\
q2doc help text
"""


# Entry point for CLI
@click.group(no_args_is_help=True, help=ROOT_COMMAND_HELP)
@click.version_option(prog_name='q2doc',
                      message='%(prog)s version %(version)s')
def root():
    pass


@root.command()
def install(book):
    pass


@root.command()
def refresh_cache():
    get_cache(refresh=True)


myst_help = """
For use by the MyST documentation system.

This is the implementation of the executable plugin for q2doc:

    https://mystmd.org/guide/executable-plugins
"""

@root.command(help=myst_help)
@click.option('--directive', type=str, default=None)
@click.option('--transform', type=str, default=None)
@click.argument('stdin', required=False, type=click.File(), default=sys.stdin)
def myst(directive, transform, stdin):
    if directive:
        result = run_directive(directive, json.load(stdin))
    elif transform:
        result = run_transform(transform, json.load(stdin))
    else:
        result = dict(name='q2doc', **spec_directives(), **spec_transforms())

    print(json.dumps(result, indent=2), flush=True, file=sys.stdout)



@root.command()
@click.argument('book')
def autodoc(book):
    if not is_book(book):
        raise ValueError('book')

    write_plugin(book, 'types')
    write_bibtex(book, refresh=False)

if __name__ == '__main__':
    root()