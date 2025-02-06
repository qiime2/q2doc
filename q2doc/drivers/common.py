import os
import urllib

def _build_url(data_dir, fn):
    baseurl = os.environ.get('BASE_URL')
    if baseurl is None:
        baseurl = os.environ.get('READTHEDOCS_CANONICAL_URL')
    if baseurl is None:
        # prevent myst from treating it as a local ref (and clobbering the url)
        baseurl = '/'

    parts = list(urllib.parse.urlparse(baseurl))
    parts[2] += '/'.join([str(data_dir), str(fn)])
    url = urllib.parse.urlunparse(parts)
    return url