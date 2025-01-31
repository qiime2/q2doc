
import q2doc.myst as md
from .common import DirectiveHandler

class DescribeUsage(DirectiveHandler):
    """A directive to describe a QIIME 2 usage example."""
    name = 'describe-usage'
    arg_help = 'No arguments'

    @classmethod
    def cache_all(cls, pm):
        return None

    @classmethod
    def get_options(cls):
        return {
            'scope': dict(
                type='string',
                help='A directory where results will be saved. Will be treated as a unique namespace'
            )
        }

    @classmethod
    def apply_options(cls, ast, node, scope=None):
        ast = md.code_ast('python', node['value'])
        ast['data'] = dict(deferred=True, scope=scope, source='describe-usage')
        return [ast]