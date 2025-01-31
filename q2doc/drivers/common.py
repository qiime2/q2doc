import os
import urllib

def _build_url(data_dir, fn):
    baseurl = os.environ.get('BASE_URL', '/')
    parts = list(urllib.parse.urlparse(baseurl))
    parts[2] += '/'.join([str(data_dir), str(fn)])
    url = urllib.parse.urlunparse(parts)
    return url