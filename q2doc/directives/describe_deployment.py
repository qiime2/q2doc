
import q2doc.myst as md
from .common import DirectiveHandler, plugin_to_id

class DescribeDeployment(DirectiveHandler):
    """A directive to describe a QIIME 2 Deployment."""
    name = 'describe-deployment'
    arg_help = 'No arguments'

    @classmethod
    def cache_all(cls, pm):
        ast = {}

        rows = []
        for name, plugin in sorted(pm.plugins.items(), key=lambda x: x[0]):
            rows.append([md.cross_reference_ast(md.inline_code_ast(plugin.name),
                                                id=plugin_to_id(plugin)),
                         plugin.short_description])

        return [md.table_ast(rows, col_headers = ['Name', 'Short Description'])]
