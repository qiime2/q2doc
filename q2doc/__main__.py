# ----------------------------------------------------------------------------
# Copyright (c) 2025, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import click


ROOT_COMMAND_HELP = """\
q2doc help text
"""


# Entry point for CLI
@click.command(no_args_is_help=True, help=ROOT_COMMAND_HELP)
@click.version_option(prog_name='q2doc',
                      message='%(prog)s version %(version)s')
def root():
    pass


if __name__ == '__main__':
    root()