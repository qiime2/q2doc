import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
from contextlib import closing, contextmanager

from q2doc import __version__


_USER_AGENT = f'q2doc/{__version__} (+https://qiime2.org)'


class ZenodoURLMixin:
    _ZENODO_TOKEN_ENV_VAR = 'ZENODO_API_TOKEN'
    _ZENODO_HINT_HTTP_STATUS_CODES = {401, 403, 429}
    _ZENODO_TOKEN_HINT = (
        'Zenodo appears to have rate-limited or blocked anonymous access to '
        'this file. Setting `ZENODO_API_TOKEN` to a free Zenodo personal '
        'access token (PAT) will resolve this problem.'
    )

    def _is_zenodo_url(self, url):
        parsed = urllib.parse.urlparse(url)
        return (
            parsed.scheme == 'https'
            and (
                parsed.netloc == 'zenodo.org'
                or parsed.netloc.endswith('.zenodo.org')
            )
        )

    def _has_zenodo_token(self):
        return bool(os.environ.get(self._ZENODO_TOKEN_ENV_VAR))

    def _should_add_zenodo_hint(self, url, status_code):
        return (
            self._is_zenodo_url(url)
            and not self._has_zenodo_token()
            and status_code in self._ZENODO_HINT_HTTP_STATUS_CODES
        )

    def _request_url(self, url):
        headers = {
            'User-Agent': _USER_AGENT
        }

        if self._is_zenodo_url(url):
            token = os.environ.get(self._ZENODO_TOKEN_ENV_VAR)
            if token:
                headers['Authorization'] = f'Bearer {token}'

        try:
            request = urllib.request.Request(url, headers=headers)
            data = urllib.request.urlopen(request)
        except urllib.error.HTTPError as ex:
            message = f'Could not obtain URL: {url}'
            if self._should_add_zenodo_hint(url, ex.code):
                message += '\n ' + self._ZENODO_TOKEN_HINT
            raise ValueError(message) from ex
        except urllib.error.URLError as ex:
            raise ValueError(f'Could not obtain URL: {url}') from ex

        return data

    @contextmanager
    def _materialize_url(self, url):
        import tempfile

        with tempfile.NamedTemporaryFile() as fh:
            with closing(self._request_url(url)) as data:
                shutil.copyfileobj(data, fh)

            # copyfileobj may leave data in fh's buffer; flush before a loader
            # reopens the same path through a separate file handle.
            fh.flush()
            yield fh.name

    def init_artifact_from_url(self, name, url):
        import qiime2

        def factory():
            with self._materialize_url(url) as fp:
                try:
                    result = qiime2.Artifact.load(fp)
                except Exception as ex:
                    raise ValueError(
                        f'Could not load Artifact from URL data: {url}'
                    ) from ex

            return result

        return self.init_artifact(name, factory)

    def init_metadata_from_url(self, name, url):
        import qiime2

        def factory():
            with self._materialize_url(url) as fp:
                try:
                    result = qiime2.Metadata.load(fp)
                except Exception as ex:
                    raise ValueError(
                        f'Could not load Metadata from URL data: {url}'
                    ) from ex

            return result

        return self.init_metadata(name, factory)
