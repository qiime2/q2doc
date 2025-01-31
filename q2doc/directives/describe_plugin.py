import q2doc.myst as md
from .common import DirectiveHandler, format_paragraphs, format_text, plugin_to_id, action_to_id, type_to_id, format_to_id, format_citations

class DescribePlugin(DirectiveHandler):
    """A directive to describe a QIIME 2 plugin's available types and actions."""
    name = 'describe-plugin'
    arg_help = 'Format as: <plugin>'

    @classmethod
    def cache_all(cls, pm):
        ast = {}

        for name, plugin in pm.plugins.items():
            ast[name] = cls.format_record(name, plugin)

        return ast

    @classmethod
    def format_record(cls, name, plugin):
        ast = [md.heading_ast(1, name, id=plugin_to_id(plugin))]
        ast.extend(format_paragraphs(plugin.description))

        citations = []
        if plugin.citations:
            citations = [(md.kv_header_ast('citations', ''),
                          format_citations(plugin_to_id(plugin), plugin.citations))]


        ast.append(md.definition_list_ast([
            (md.kv_header_ast('version', md.inline_code_ast(plugin.version)), None),
            (md.kv_header_ast('website', md.link_ast(plugin.website, plugin.website)), None),
            (md.kv_header_ast('user support', ''), format_text(plugin.user_support_text)),
        ] + citations))
        ast.append(md.heading_ast(2, 'Actions', id=False))
        rows = []
        for name, action in plugin.actions.items():
            plugin_name = md.cross_reference_ast(name.replace('_','-'), action_to_id(action))
            if action.deprecated:
                plugin_name = md.text_ast(plugin_name, style='delete')
            rows.append([
                plugin_name,
                md.text_ast(action.type),
                md.text_ast(action.name)
            ])
        ast.append(md.table_ast(rows, col_headers=['Name', 'Type', 'Short Description']))

        if plugin.artifact_classes:
            rows = []
            ast.append(md.heading_ast(2, 'Artifact Classes', id=False))
            for key in plugin.artifact_classes:
                rows.append([
                    md.cross_reference_ast(md.inline_code_ast(key), type_to_id(key))
                ])
            ast.append(md.table_ast(rows))

        if plugin.formats:
            rows = []
            ast.append(md.heading_ast(2, 'Formats', id=False))
            for key in plugin.formats:
                rows.append([
                    md.cross_reference_ast(md.inline_code_ast(key), format_to_id(key))
                ])
            ast.append(md.table_ast(rows))

        return ast

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
        heading = ast[0]
        heading['depth'] = depth
        return ast