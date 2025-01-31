import inspect
import textwrap
import q2doc.myst as md
from .common import DirectiveHandler, type_to_id, format_text, action_to_id, plugin_to_id, format_citations


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
                ast[name] = cls.format_record(name, action, plugin)

        return ast

    @classmethod
    def format_type(cls, qiime_type, path=()):
        import qiime2.sdk.util as util
        from qiime2.plugin import Str
        null_predicate = Str.full_predicate

        ast = []
        if util.is_union(qiime_type):
            first = True
            for inner in qiime_type.members:
                if not first:
                    ast.append(md.inline_code_ast(' | '))
                first = False
                ast.extend(cls.format_type(inner, path))
            return ast

        if (util.is_primitive_type(qiime_type)
                or util.is_visualization_type(qiime_type)
                or util.is_collection_type(qiime_type)):
            url = f'xref:qiime2#qiime2.plugin.{qiime_type.name}'
            ast.append(md.link_ast(md.inline_code_ast(qiime_type.name), url))

            if qiime_type.fields:
                ast.append(md.inline_code_ast('['))
                first = True
                for field in qiime_type.fields:
                    if not first:
                        ast.append(md.inline_code_ast(', '))
                    first = False
                    ast.extend(cls.format_type(field, ()))
                ast.append(md.inline_code_ast(']'))
        else:
            if path == () and list(qiime_type)[0].equals(qiime_type):
                temp = str(qiime_type.duplicate(predicate=null_predicate))
                ast.append(md.cross_reference_ast(md.inline_code_ast(temp), id=type_to_id(temp)))
            else:
                return [md.inline_code_ast(str(qiime_type))]

        if qiime_type.predicate:
            url = f'xref:qiime2#qiime2.plugin.{qiime_type.predicate.name}'
            ast.append(md.inline_code_ast(' % '))
            ast.append(md.link_ast(md.inline_code_ast(str(qiime_type.predicate.name)), url))
            ast.append(md.inline_code_ast(str(qiime_type.predicate)[len(qiime_type.predicate.name):]))

        return ast

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

            description = ['<no description>']
            if spec.has_description():
                description = format_text(spec.description)

            if spec.has_default():
                if spec.default is None:
                    required = '[optional]'
                else:
                    required = [md.text_ast('[default: '),
                                md.inline_code_ast(repr(spec.default)),
                                md.text_ast(']')]
            else:
                required = '[required]'
            required = md.span_ast(required, {'color': 'purple', 'float':'right'})

            params.append((term, md.paragraph_ast(description + [required])))
        return [
            md.heading_ast(2, title, id=False),
            md.definition_list_ast(params)
        ]


    @classmethod
    def format_record(cls, name, action, plugin):
        plugin_name, action_name = name.split(' ')

        desc = []
        if action.deprecated:
            desc.append(md.admonition_ast('This action is deprecated and may be removed in a future version.', title='Deprecated', kind='attention'))
        if action.description is not None:
            desc.append(md.paragraph_ast(format_text(action.description)))

        citations = []
        if plugin.citations or action.citations:
            plugin_citations = format_citations(plugin_to_id(plugin), plugin.citations)
            action_citations = format_citations(action_to_id(action), action.citations)
            combined_citations = plugin_citations
            if plugin_citations and action_citations:
                combined_citations += [md.text_ast('; ')]
            combined_citations += action_citations

            citations = [
                md.heading_ast(2, 'Citations', id=False),
                md.paragraph_ast(combined_citations)
            ]

        examples = []
        if action.examples:
            examples.append(md.heading_ast(2, 'Examples', id=False))
            for idx, (name, func) in enumerate(action.examples.items(), 1):
                val = textwrap.dedent(f"""
                    from {func.__module__} import {func.__name__}

                    {func.__name__}(use)
                """)
                code = md.code_ast('python', val)
                code['data'] = dict(deferred=True, scope=f'examples/{plugin_name}/{action_name}/{idx}', source='describe-usage')
                examples.append(md.heading_ast(3, name, id=False))
                examples.append(code)


        return (
            [md.heading_ast(1, [md.cross_reference_ast(plugin_name, id=plugin_to_id(plugin_name)), md.text_ast(' '), md.text_ast(action_name)], id=action_to_id(action))]
            + desc
            + citations
            + cls.format_signature('Inputs', action.signature.inputs)
            + cls.format_signature('Parameters', action.signature.parameters)
            + cls.format_signature('Outputs', action.signature.outputs)
            + examples
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
    def apply_options(cls, ast, node, skip_heading=False):
        if skip_heading:
            heading = ast[0]
            ast[0] = md.target_ast(heading['label'])
        return ast

