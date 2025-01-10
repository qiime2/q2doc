import q2doc.myst as md
from .common import DirectiveHandler, type_to_id

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
        return [
            md.heading_ast(1, name, id=type_to_id(name)),
            md.paragraph_ast(record.description)
        ]
