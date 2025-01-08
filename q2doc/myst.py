import json
import sys


DESCRIBE_ARTIFACT = {
    'name': 'describe-artifact',
    'doc': 'A directive to describe a QIIME 2 artifact class.',
    'arg': {
        'type': 'string',
        'doc': 'Format as: <plugin-name> <Semantic[Type]>'
    },
    'options': {}
}


def describe_artifact(directive, plugin_name, name):
    assert directive == 'describe-artifact'

    from qiime2.sdk import PluginManager
    pm = PluginManager()
    plugin = pm.get_plugin(name=plugin_name)
    record = plugin.artifact_classes[name]
    return [
            {'type': 'heading', 'depth':1, 'identifier': f'q2doc-{plugin_name}-{name}', 'label': name, 'children': [{'type': 'text', 'value': name}]},
            {'type': 'paragraph', 'children': [{'type': 'text', 'value': record.description}]}
        ]

lookup = {
    'describe-artifact': describe_artifact,
}
spec = {
    "name": "q2doc",
    "directives": [
        DESCRIBE_ARTIFACT,
    ],
}


def run_spec():
    return spec


def run_directive(directive, data):
    options = data['options']
    plugin, object = data['arg'].split(' ')
    return lookup[directive](directive, plugin, object, **options)
