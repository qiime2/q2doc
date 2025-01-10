import q2doc.myst as md
from .common import DirectiveHandler

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
        desc = []
        if record.format.__doc__ is not None:
            desc = [md.paragraph_ast(record.format.__doc__)]
        return [
            md.heading_ast(1, name, id=f'q2-{record.plugin.name}-{name}'),
        ] + desc