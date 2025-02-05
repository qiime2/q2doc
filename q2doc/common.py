import os

from q2doc.directives.common import plugin_to_id, action_to_id, format_to_id
import q2doc.myst as md
from .cache import get_cache

def is_book(dir):
    return os.path.isdir(dir) and os.path.isfile(os.path.join(dir, 'myst.yml'))


def write_bibtex(dir, refresh=True):
    _ = get_cache(refresh=refresh)

    from qiime2.sdk import PluginManager, Citations
    pm = PluginManager()


    citations = Citations()
    for plugin in pm.plugins.values():
        for idx, entry in enumerate(plugin.citations):
            citations[f'{plugin_to_id(plugin)}-{idx}'] = entry
        for action in plugin.actions.values():
            for idx, entry in enumerate(action.citations):
                citations[f'{action_to_id(action)}-{idx}'] = entry
        for view in plugin.views.values():
            for idx, entry in enumerate(view.citations):
                citations[f'{format_to_id(view.name)}-{idx}'] = entry
    citations.save(os.path.join(dir, 'q2doc.bib'))


def write_plugin(dir, plugin_name):
    _ = get_cache(refresh=True)

    from qiime2.sdk import PluginManager
    pm = PluginManager()

    root = os.path.join(dir, 'Plugin-Reference')
    os.makedirs(root, exist_ok=True)

    action_root = os.path.join(root, 'plugins')
    os.makedirs(action_root, exist_ok=True)
    for name, plugin in pm.plugins.items():
        plugin_root = os.path.join(action_root, name)
        os.makedirs(plugin_root, exist_ok=True)
        with open(os.path.join(plugin_root, 'index.md'), 'w') as fh:
            fh.write(md.frontmatter_yml(title="Plugin Overview"))
            fh.write(md.directive_md('describe-plugin', name))

        if not plugin.actions:
            continue

        for idx, action in enumerate(plugin.actions):
            action = action.replace('_', '-')
            with open(os.path.join(plugin_root, f'{idx}-{action}.md'), 'w') as fh:
                fh.write(md.frontmatter_yml(title=action))
                fh.write(md.directive_md('describe-action', f'{name} {action}'))

    artifacts_root = os.path.join(root, 'artifacts')
    os.makedirs(artifacts_root, exist_ok=True)

    with open(os.path.join(artifacts_root, 'classes.md'), 'w') as fh:
        fh.write('# Artifact Classes\n\n')
        for name, plugin in pm.plugins.items():
            if not plugin.artifact_classes:
                continue

            fh.write(f'## __[{name}](#{plugin_to_id(plugin)})__\n\n')
            fh.write('---\n\n')
            for key in plugin.artifact_classes:
                fh.write(md.directive_md('describe-artifact', key, depth=3))
            fh.write('\n---\n\n')

    with open(os.path.join(artifacts_root, 'formats.md'), 'w') as fh:
        fh.write('# Formats\n\n')
        for name, plugin in pm.plugins.items():
            if not plugin.formats:
                continue

            fh.write(f'## __[{name}](#{plugin_to_id(plugin)})__\n\n')
            fh.write('---\n\n')
            for key in plugin.formats:
                fh.write(md.directive_md('describe-format', key, depth=3))
            fh.write('\n---\n\n')