from q2doc.cache import get_cache

from .describe_action import DescribeAction
from .describe_artifact import DescribeArtifact
from .describe_format import DescribeFormat
from .describe_plugin import DescribePlugin
from .describe_usage import DescribeUsage


DIRECTIVES = [
    DescribeArtifact,
    DescribeFormat,
    DescribeAction,
    DescribePlugin,
    DescribeUsage
]
HANDLERS = { h.name: h for h in DIRECTIVES }


def spec_directives():
    return dict(directives=[d.as_spec() for d in DIRECTIVES])


def run_directive(directive, data):
    cache = get_cache()
    arg = data.get('arg')
    options = data['options']
    node = data['node']

    if arg is None:
        ast = None
    else:
        ast = cache[directive][arg]
    ast = HANDLERS[directive].apply_options(ast, node, **options)

    return ast
