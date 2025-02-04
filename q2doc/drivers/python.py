from qiime2.plugins import ArtifactAPIUsage
from q2cli.core.usage import CLIUsageVariable

from .common import _build_url
import q2doc.myst as md


class MystPythonUsage(ArtifactAPIUsage):
    def __init__(self, data_dir, auto_collect_size):
        super().__init__(action_collection_size=auto_collect_size)
        self.scope = dict(use=self)
        self.data_dir = data_dir

    def _to_cli_var(self, var):
        # Build a tmp cli-based variable, for filename templating!
        return CLIUsageVariable(var.name, lambda: None, var.var_type, var.use)

    def _download_file(self, var):
        cli_var = self._to_cli_var(var)
        fn = cli_var.to_interface_name()
        url = _build_url(self.data_dir, fn)

        self._update_imports(from_='urllib', import_='request')

        lines = [
            'url = %r' % (url,),
            'fn = %r' % (fn,),
            'request.urlretrieve(url, fn)',
        ]

        self._add(lines)

        return cli_var

    def init_artifact(self, name, factory):
        var = super().init_artifact(name, factory)

        self._download_file(var)
        self._update_imports(from_='qiime2', import_='Artifact')
        input_fp = var.to_interface_name()

        lines = [
            '%s = Artifact.load(fn)' % (input_fp,),
            '',
        ]

        self._add(lines)

        return var

    def init_metadata(self, name, factory):
        var = super().init_metadata(name, factory)

        self._download_file(var)
        self._update_imports(from_='qiime2', import_='Metadata')
        input_fp = var.to_interface_name()

        lines = [
            '%s = Metadata.load(fn)' % (input_fp,),
            '',
        ]

        self._add(lines)

        return var

    def init_format(self, name, factory, ext=None):
        var = super().init_format(name, factory, ext=ext)

        # no ext means a dirfmt, which means we have zipped the computed res.
        if ext is None:
            ext = 'zip'

        fn = '%s.%s' % (name, ext)
        tmp_var = self.usage_variable(fn, lambda: None, var.var_type)
        self._download_file(tmp_var)

        if ext == 'zip':
            self._update_imports(import_='zipfile')
            input_fp = var.to_interface_name()

            lines = [
                'with zipfile.ZipFile(fn) as zf:',
                '    zf.extractall(%r)' % (input_fp,)
            ]

            self._add(lines)

        return var

    def render(self, flush=False, **kwargs):
        rendered = super().render(flush)

        if rendered == '':
            return None

        return md.code_ast('python', rendered)