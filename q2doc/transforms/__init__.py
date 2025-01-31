from .transform_usage import TransformUsage
from flufl.lock import Lock
import os
import psutil
import random

TRANSFORMS = [
    TransformUsage
]
HANDLERS = { t.name: t for t in TRANSFORMS }



def spec_transforms():
    return dict(transforms=[t.as_spec() for t in TRANSFORMS])


def run_transform(name, ast):
    n_jobs = max(psutil.cpu_count() - 1, 1)
    group = random.randrange(0, n_jobs)
    os.makedirs('.locks', exist_ok=True)
    with Lock(os.path.join('.locks/', f'q2doc-{name}.{group}'), lifetime=60 * 60 * 3):
        transform = HANDLERS[name]()
        return transform.run(ast)