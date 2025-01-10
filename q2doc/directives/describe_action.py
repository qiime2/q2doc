import q2doc.myst as md
from .common import DirectiveHandler, type_to_id


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
    def format_type(cls, semantic_type):
        import qiime2.sdk.util as util
        if util.is_primitive_type(semantic_type) and not util.is_union(semantic_type):
            if util.is_collection_type(semantic_type):
                pass
            else:
                root = semantic_type.duplicate(predicate=None)
                url = f'xref:qiime2#qiime2.plugin.{root.name}'
                return [md.link_ast(root.name, url)]


        if util.is_collection_type(semantic_type) and not util.is_union(semantic_type):
            inner = semantic_type.fields[0]
            return [
                md.text_ast(semantic_type.name),
                md.text_ast('['),
                md.cross_reference_ast(str(inner), id=type_to_id(inner)),
                md.text_ast(']')
            ]
        if util.is_semantic_type(semantic_type):
            return [md.cross_reference_ast(str(semantic_type), id=type_to_id(semantic_type))]

        return [md.text_ast(str(semantic_type))]

    @classmethod
    def format_signature(cls, title, entries):
        items = list(entries.items())
        if not items:
            return []

        params = []
        for param, spec in items:
            term = [
                md.text_ast(
                    md.text_ast(param, style='underline' if not spec.has_default() else None),
                    style='strong'
                ),
                md.text_ast(': '),
            ] + cls.format_type(spec.qiime_type)

            description = '<no description>'
            if spec.has_description():
                description = spec.description

            if spec.has_default():
                if spec.default is None:
                    required = '[optional]'
                else:
                    required = f'[default: {spec.default!r}]'
            else:
                required = '[required]'
            required = md.span_ast(required, {'color': 'purple', 'float':'right'})

            params.append((term, md.paragraph_ast(description, required)))

        return [
            md.heading_ast(2, title, id=False),
            md.definition_list_ast(params)
        ]


    @classmethod
    def format_record(cls, name, action):
        desc = []
        if action.description is not None:
            desc = [md.paragraph_ast(action.description)]

        return (
            [md.heading_ast(1, name, id=f'q2-{name}')]
            + desc
            + cls.format_signature('Inputs', action.signature.inputs)
            + cls.format_signature('Parameters', action.signature.parameters)
            + cls.format_signature('Outputs', action.signature.outputs)
        )

    @classmethod
    def get_options(cls):
        return {
            'skip_heading': dict(
                type='boolean',
                help='Whether to skip the heading for the action'
            )
        }

    @classmethod
    def apply_options(cls, ast, skip_heading=False):
        if skip_heading:
            heading = ast[0]
            ast[0] = md.target_ast(heading['label'])
        return ast

