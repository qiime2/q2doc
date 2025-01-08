import os

def is_book(dir):
    return os.path.isdir(dir) and os.path.isfile(os.path.join(dir, 'myst.yml'))


def write_plugin(dir, plugin_name):
    from qiime2.sdk import PluginManager
    pm = PluginManager()
    plugin = pm.get_plugin(name=plugin_name)

    root = os.path.join(dir, 'Plugin-Reference')
    os.makedirs(root, exist_ok=True)

    action_root = os.path.join(root, 'actions')
    os.makedirs(action_root, exist_ok=True)
    for action in plugin.actions:
        action = action.replace('_', '-')
        with open(os.path.join(action_root, f'{action}.md'), 'w') as fh:
            fh.write(f'# {action}\n')

    artifacts_root = os.path.join(root, 'artifacts')
    os.makedirs(artifacts_root, exist_ok=True)

    with open(os.path.join(artifacts_root, 'classes.md'), 'w') as fh:
        fh.write('# Artifact Classes\n\n')
        for artifact_class, record in plugin.artifact_classes.items():
            fh.write(f':::{{describe-artifact}} {plugin_name} {artifact_class}'
                     '\n:::\n\n')

    with open(os.path.join(artifacts_root, 'formats.md'), 'w') as fh:
        fh.write('# Formats\n\n')
        for format in plugin.formats:
            fh.write(f'## {format}\n\n')