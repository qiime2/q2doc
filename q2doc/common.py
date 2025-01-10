import os

import q2doc.myst as md
from .cache import get_cache

def is_book(dir):
    return os.path.isdir(dir) and os.path.isfile(os.path.join(dir, 'myst.yml'))


def write_plugin(dir, plugin_name):
    _ = get_cache(refresh=True)

    from qiime2.sdk import PluginManager
    pm = PluginManager()
    plugin = pm.get_plugin(name=plugin_name)
    diversity = pm.get_plugin(name='diversity')

    root = os.path.join(dir, 'Plugin-Reference')
    os.makedirs(root, exist_ok=True)

    action_root = os.path.join(root, 'actions')
    os.makedirs(action_root, exist_ok=True)
    for action in diversity.actions:
        action = action.replace('_', '-')
        with open(os.path.join(action_root, f'{action}.md'), 'w') as fh:
            fh.write(md.frontmatter_yml(title=action))
            fh.write(md.directive_md('describe-action', f'diversity {action}'))

    artifacts_root = os.path.join(root, 'artifacts')
    os.makedirs(artifacts_root, exist_ok=True)

    with open(os.path.join(artifacts_root, 'classes.md'), 'w') as fh:
        fh.write('# Artifact Classes\n\n')
        for key in plugin.artifact_classes:
            fh.write(md.directive_md('describe-artifact', key))

    with open(os.path.join(artifacts_root, 'formats.md'), 'w') as fh:
        fh.write('# Formats\n\n')
        for key in plugin.formats:
            fh.write(md.directive_md('describe-format', key))