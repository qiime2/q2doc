from q2doc.cache import get_cache

from .describe_action import DescribeAction
from .describe_artifact import DescribeArtifact
from .describe_format import DescribeFormat


DIRECTIVES = [
    DescribeArtifact,
    DescribeFormat,
    DescribeAction
]
HANDLERS = { h.name: h for h in DIRECTIVES }


def run_spec():
    return dict(name='q2doc', directives=[d.as_spec() for d in DIRECTIVES])


def run_directive(directive, data):
    cache = get_cache()
    arg = data['arg']
    options = data['options']

    ast = cache[directive][arg]
    ast = HANDLERS[directive].apply_options(ast, **options)

    return ast
