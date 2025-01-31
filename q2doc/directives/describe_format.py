import q2doc.myst as md
from .common import DirectiveHandler, format_paragraphs, format_to_id, plugin_to_id

class DescribeFormat(DirectiveHandler):
    """A directive to describe a QIIME 2 file/directory format."""
    name = 'describe-format'
    arg_help = 'Format as: <FileFormat>'

    @classmethod
    def cache_all(cls, pm):
        ast = {}

        for name, record in pm.formats.items():
            ast[name] = cls.format_record(name, record)

        return ast

    @classmethod
    def format_record(cls, name, record):
        from qiime2.plugin import TextFileFormat, BinaryFileFormat, DirectoryFormat

        header = md.heading_ast(1, md.inline_code_ast(name), id=format_to_id(name))

        ast = []
        ast.extend(format_paragraphs(record.format.__doc__ or ''))

        if (issubclass(record.format, DirectoryFormat)):
            table_rows = []
            for name in record.format._fields:
                field = getattr(record.format, name)
                table_rows.append([
                    name,
                    md.inline_code_ast(field.pathspec),
                    md.cross_reference_ast(md.inline_code_ast(field.format.__name__),
                                           format_to_id(field.format)),
                str(not field.optional)
                ])

            ast.append(md.definition_list_ast([
                (md.kv_header_ast('plugin', md.cross_reference_ast(record.plugin.id.replace('_', '-'), id=plugin_to_id(record.plugin))), None),
                (md.kv_header_ast('type', 'directory'), None),
                (md.kv_header_ast('files', ''), md.table_ast(
                    table_rows,
                    col_headers=['name', 'path', 'format', 'required']))
            ]))
        elif issubclass(record.format, BinaryFileFormat):
            ast.append(md.kv_list_ast({'type': 'binary file'}))
        elif issubclass(record.format, TextFileFormat):
            ast.append(md.kv_list_ast({'type': 'text file'}))
        else:
            raise AssertionError(f'Unreachable branch {name} {record}')


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
        heading = ast[0]
        heading['depth'] = depth
        return ast