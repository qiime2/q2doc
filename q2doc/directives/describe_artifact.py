import q2doc.myst as md
from .common import DirectiveHandler, type_to_id, format_to_id, plugin_to_id, format_paragraphs

class DescribeArtifact(DirectiveHandler):
    """A directive to describe a QIIME 2 artifact class."""
    name = 'describe-artifact'
    arg_help = 'Format as: <Semantic[Type]>'

    @classmethod
    def cache_all(cls, pm):
        ast = {}

        for name, record in pm.artifact_classes.items():
            ast[name] = cls.format_record(name, record)

        return ast

    @classmethod
    def format_record(cls, name, record):
        from qiime2.sdk import PluginManager
        header = md.heading_ast(1, md.inline_code_ast(name), id=type_to_id(name))
        ast = format_paragraphs(record.description)
        # ast.append(md.kv_list_ast({
        #         'format':
        #             md.cross_reference_ast(md.inline_code_ast(record.format.__name__),
        #                                    id=format_to_id(record.format))
        #     }))

        rows = []
        pm = PluginManager.reuse_existing()
        all_formats = pm.get_formats(semantic_type=name)
        importable = pm.get_formats(filter='IMPORTABLE', semantic_type=name)
        exportable = pm.get_formats(filter='EXPORTABLE', semantic_type=name)
        rows = [[md.cross_reference_ast(md.inline_code_ast(name), id=format_to_id(name)), '✔' if name in importable else '', '✔' if name in exportable else '']
                for name in all_formats]

        ast.append(md.definition_list_ast([
            (md.kv_header_ast('plugin', md.cross_reference_ast(record.plugin.id.replace('_', '-'), id=plugin_to_id(record.plugin))), None),
            (md.kv_header_ast('format', md.cross_reference_ast(md.inline_code_ast(record.format.__name__), id=format_to_id(record.format))), None),
            (md.kv_header_ast('transformers', ''), md.table_ast(rows, col_headers=['view', 'import', 'export']))
        ]))

        return [header, md.div_ast(ast, classes='col-body-inset')]

    @classmethod
    def get_options(cls):
        return {
            'depth': dict(
                type='number',
                help='Depth of the heading'
            )
        }

    @classmethod
    def apply_options(cls, ast, node, depth=1):
        for node in ast:
            if node['type'] == 'heading':
                node['depth'] = depth + (node['depth'] - 1)
            elif 'children' in node:
                for child in node['children']:
                    cls.apply_options([child], depth)
        return ast
