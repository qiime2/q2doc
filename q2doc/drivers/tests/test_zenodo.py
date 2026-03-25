import os
import sys
import types
import urllib.error
import unittest
from unittest import mock

from q2doc.drivers.zenodo import ZenodoURLMixin


class _Response:
    def __init__(self, payload=b'payload'):
        self.payload = payload
        self._offset = 0

    def read(self, size=-1):
        if size is None or size < 0:
            size = len(self.payload) - self._offset

        chunk = self.payload[self._offset:self._offset + size]
        self._offset += len(chunk)
        return chunk

    def close(self):
        pass


class _DummyUsage(ZenodoURLMixin):
    def init_artifact(self, name, factory):
        self.artifact_factory = factory
        return factory

    def init_metadata(self, name, factory):
        self.metadata_factory = factory
        return factory


class ZenodoURLMixinTests(unittest.TestCase):
    def setUp(self):
        self.use = _DummyUsage()
        self.zenodo_url = 'https://zenodo.org/records/1/files/example.qza'

    def test_request_url_adds_bearer_token_for_zenodo(self):
        with mock.patch.dict(
            os.environ, {'ZENODO_API_TOKEN': 'secret-token'}, clear=True
        ):
            with mock.patch(
                'urllib.request.urlopen', return_value=_Response()
            ) as urlopen:
                self.use._request_url(self.zenodo_url)

        request = urlopen.call_args.args[0]
        self.assertEqual(
            dict(request.header_items())['Authorization'],
            'Bearer secret-token'
        )
        self.assertRegex(
            dict(request.header_items())['User-agent'],
            r'^q2doc/.+ \(\+https://qiime2\.org\)$'
        )

    def test_request_url_without_token_has_actionable_zenodo_error(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch(
                'urllib.request.urlopen',
                side_effect=urllib.error.HTTPError(
                    self.zenodo_url, 403, 'Forbidden', hdrs=None, fp=None
                )
            ):
                with self.assertRaisesRegex(
                    ValueError, 'ZENODO_API_TOKEN'
                ) as ctx:
                    self.use._request_url(self.zenodo_url)

        message = str(ctx.exception)
        self.assertIn('rate-limited or blocked', message)
        self.assertIn('free Zenodo personal access token', message)
        self.assertIsInstance(ctx.exception.__cause__, urllib.error.HTTPError)

    def test_request_url_without_token_404_has_no_zenodo_hint(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch(
                'urllib.request.urlopen',
                side_effect=urllib.error.HTTPError(
                    self.zenodo_url, 404, 'Not Found', hdrs=None, fp=None
                )
            ):
                with self.assertRaisesRegex(
                    ValueError, 'Could not obtain URL'
                ) as ctx:
                    self.use._request_url(self.zenodo_url)

        self.assertNotIn('ZENODO_API_TOKEN', str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, urllib.error.HTTPError)

    def test_init_artifact_from_url_load_error_has_no_zenodo_guidance(self):
        fake_qiime2 = types.ModuleType('qiime2')

        class Artifact:
            @staticmethod
            def load(path):
                raise ValueError('not a QIIME archive')

        fake_qiime2.Artifact = Artifact

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.dict(sys.modules, {'qiime2': fake_qiime2}):
                with mock.patch(
                    'urllib.request.urlopen', return_value=_Response()
                ):
                    factory = self.use.init_artifact_from_url(
                        'artifact', self.zenodo_url
                    )

                    with self.assertRaisesRegex(
                        ValueError, 'Could not load Artifact from URL data'
                    ) as ctx:
                        factory()

        self.assertNotIn('ZENODO_API_TOKEN', str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, ValueError)
        self.assertEqual(str(ctx.exception.__cause__), 'not a QIIME archive')

    def test_init_metadata_from_url_load_error_has_no_zenodo_guidance(self):
        fake_qiime2 = types.ModuleType('qiime2')
        fake_qiime2.__path__ = []
        fake_metadata = types.ModuleType('qiime2.metadata')
        fake_metadata.__path__ = []
        fake_metadata_io = types.ModuleType('qiime2.metadata.io')

        class MetadataFileError(Exception):
            pass

        class Metadata:
            @staticmethod
            def load(path):
                raise MetadataFileError('not metadata')

        fake_qiime2.Metadata = Metadata
        fake_qiime2.metadata = fake_metadata
        fake_metadata.io = fake_metadata_io
        fake_metadata_io.MetadataFileError = MetadataFileError

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.dict(
                sys.modules,
                {
                    'qiime2': fake_qiime2,
                    'qiime2.metadata': fake_metadata,
                    'qiime2.metadata.io': fake_metadata_io,
                }
            ):
                with mock.patch(
                    'urllib.request.urlopen', return_value=_Response()
                ):
                    factory = self.use.init_metadata_from_url(
                        'metadata', self.zenodo_url
                    )

                    with self.assertRaisesRegex(
                        ValueError, 'Could not load Metadata from URL data'
                    ) as ctx:
                        factory()

        self.assertNotIn('ZENODO_API_TOKEN', str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, MetadataFileError)
        self.assertEqual(str(ctx.exception.__cause__), 'not metadata')
