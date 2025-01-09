import q2doc.myst as md
from .cache import get_cache


class DirectiveHandler:
    @classmethod
    def as_spec(cls):
        return dict(name=cls.name,
                    doc=cls.__doc__,
                    arg=dict(type='string', doc=cls.arg_help),
                    options=cls.get_options())

    @classmethod
    def get_options(cls):
        return {}


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
            md.heading_ast(name, id=f'q2-{record.plugin.name}-{name}'),
            md.paragraph_ast(record.description)
        ]


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
            md.heading_ast(name, id=f'q2-{record.plugin.name}-{name}'),
        ] + desc


class DescribeAction(DirectiveHandler):
    """A directive to describe a QIIME 2 action."""
    name = 'describe-action'
    arg_help = 'Format as: <plugin-name> <action-name>'

    @classmethod
    def cache_all(cls, pm):
        ast = {}

        for plugin_name, plugin in pm.plugins.items():
            for action_name, action in plugin.actions.items():
                action_name = action.id.replace('_', '-')
                name = ' '.join([plugin_name, action_name])
                ast[name] = cls.format_record(name, action)

        return ast

    @classmethod
    def format_record(cls, name, action):
        desc = []
        if action.description is not None:
            desc = [md.paragraph_ast(action.description)]
        return [
            md.heading_ast(name, id=f'q2-{name}'),
        ] + desc

DIRECTIVES = [
    DescribeArtifact,
    DescribeFormat,
    DescribeAction
]


def run_spec():
    return dict(name='q2doc', directives=[d.as_spec() for d in DIRECTIVES])


def run_directive(directive, data):
    cache = get_cache()
    arg = data['arg']
    return cache[directive][arg]
