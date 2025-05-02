from qiime2.sdk.usage import Usage
from q2cli.core.usage import CLIUsage
import q2doc.myst as md

from .common import _build_url


class MystCLIUsage(CLIUsage):
    def __init__(self, data_dir, auto_collect_size):
        super().__init__(action_collection_size=auto_collect_size)
        self.scope = dict(use=self)
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

    def construct_artifact_collection(self, name, members):
        # HACK: use shortcut in the usagevar specific to q2cli
        variable = Usage.construct_artifact_collection(
            self, name, members
        )
        variable._members = members  # save for later
        variable._q2cli_ref = ' '.join([f'{key}:{value.to_interface_name()}'
                                        for (key, value) in members.items()])

        return variable

    def get_artifact_collection_member(self, name, variable, key):
        # HACK: identify implicit construction and ignore it
        if hasattr(variable, '_q2cli_ref'):
            return variable._members[key]

        return super().get_artifact_collection_member(name, variable, key)

    def render(self, flush=False, **kwargs):
        rendered = super().render(flush)

        if rendered == '':
            return None

        return md.code_ast('bash', rendered)
