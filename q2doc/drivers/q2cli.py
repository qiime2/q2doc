from q2cli.core.usage import CLIUsage
import q2doc.myst as md

from .common import _build_url

class MystCLIUsage(CLIUsage):
    def __init__(self, data_dir, auto_collect_size):
        super().__init__(action_collection_size=auto_collect_size)
        self.data_dir = data_dir

    def _download_file(self, var):
        fn = var.to_interface_name()

        url = _build_url(self.data_dir, fn)

        self.recorder.append('wget -O %r \\' % fn)
        self.recorder.append('  %r' % url)
        self.recorder.append('')

    def init_artifact(self, name, factory):
        var = super().init_artifact(name, factory)
        self._download_file(var)
        return var

    def init_metadata(self, name, factory):
        var = super().init_metadata(name, factory)
        self._download_file(var)
        return var

    def init_format(self, name, factory, ext=None):
        var = super().init_format(name, factory, ext=ext)

        # no ext means a dirfmt, which means we have zipped the computed res.
        if ext is None:
            ext = 'zip'

        fn = '%s.%s' % (name, ext)
        cli_var = self.usage_variable(fn, lambda: None, var.var_type)
        self._download_file(cli_var)

        if ext == 'zip':
            zip_fp = var.to_interface_name()
            out_fp = cli_var.to_interface_name()
            self.recorder.append('unzip -d %s %s' % (zip_fp, out_fp))

        return var

    def render(self, flush=False, **kwargs):
        rendered = super().render(flush)

        if rendered == '':
            return None

        return md.code_ast('bash', rendered)
