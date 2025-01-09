import os
import json

import click
from q2doc import __version__


def get_app_dir():
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix is not None:
        path = os.path.join(conda_prefix, 'var', 'q2doc')
        if os.path.exists(path) or os.access(conda_prefix, os.W_OK | os.X_OK):
            return path

    return click.get_app_dir('q2cli', roaming=False)


def get_cache_dir():
    import os.path
    return os.path.join(get_app_dir(), 'cache')


def _get_distro_versions():
    import importlib.metadata as meta
    versions = [('q2doc', __version__)]
    for entry in meta.entry_points(group='qiime2.plugins'):
        pkg = entry.module.split('.')[0]
        ver = meta.version(pkg)
        versions.append((pkg, ver))
    return sorted(versions)


def _read_requirements(file):
    '''Not a complete parser'''
    reqs = []
    if not os.path.exists(file):
        return reqs

    with open(file) as fh:
        for line in fh:
            pkg, ver = line.split('==')
            reqs.append((pkg.strip(), ver.strip()))

    return reqs


def _write_requirements(file, reqs):
    '''Not a complete writer'''
    with open(file, 'w') as fh:
        for pkg, ver in reqs:
            fh.write(f'{pkg}=={ver}\n')


def _refresh_cache(file):
    from qiime2.sdk import PluginManager
    from .directives import DIRECTIVES
    ast = {}

    pm = PluginManager()
    for handler in DIRECTIVES:
        ast[handler.name] = handler.cache_all(pm)
    with open(file, 'w') as fh:
        json.dump(ast, fh, indent=2)


def get_cache(refresh=False):
    dir = get_cache_dir()
    reqs_fp = os.path.join(dir, 'requirements.txt')
    cache_fp = os.path.join(dir, 'myst-ast.json')

    curr = _get_distro_versions()
    last = _read_requirements(reqs_fp)

    if curr != last or refresh:
        os.makedirs(dir, exist_ok=True)
        _refresh_cache(cache_fp)
        _write_requirements(reqs_fp, curr)

    try:
        with open(cache_fp) as fh:
            ast = json.load(fh)
    except Exception:
        _refresh_cache(cache_fp)
        _write_requirements(reqs_fp, curr)
        with open(cache_fp) as fh:
            ast = json.load(fh)

    return ast