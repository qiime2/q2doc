import os
import io
import urllib
import pathlib
import shutil
import tempfile
from contextlib import redirect_stderr, redirect_stdout, contextmanager

from qiime2.util import redirected_stdio
from qiime2.plugin import model
from qiime2.sdk.usage import Usage, ExecutionUsageVariable

from q2cli.core.usage import CLIUsage, CLIUsageVariable

import q2doc.myst as md

from .common import _build_url




class MystExecUsageVariable(ExecutionUsageVariable, CLIUsageVariable):
    # ExecutionUsageVariable knows how to assert results
    # CLIUsageVariable knows how to build filesystem filenames
    pass


class MystExecUsage(Usage):
    def __init__(self, data_dir, auto_collect_size):
        super().__init__()
        self.recorder = {}
        self.data_dir = pathlib.Path(data_dir)
        self.auto_collect_size = auto_collect_size
        self.cli_use = CLIUsage()
        self.stdout = tempfile.TemporaryFile()
        self.stderr = tempfile.TemporaryFile()
        self.misc_nodes = []

    def usage_variable(self, name, factory, var_type):
        return MystExecUsageVariable(name, factory, var_type, self)

    def _add_record(self, variable):
        with redirected_stdio(stdout=self.stdout, stderr=self.stderr):
            result = variable.execute()
            iname = variable.to_interface_name()
            self.recorder[iname] = result
        return variable

    def _save_results(self):
        with redirected_stdio(stdout=self.stdout,
                                stderr=self.stderr):
            fns = {}
            for fn, result in self.recorder.items():
                fp = str(self.data_dir / fn)
                if type(result) is str:
                    os.symlink(result, fp)
                elif isinstance(result, model.DirectoryFormat):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmpdir = pathlib.Path(tmpdir)
                        result.save(tmpdir / 'dirfmt')
                        fp = shutil.make_archive(fp, 'zip', str(result))
                else:
                    fp = result.save(fp)
                fp = pathlib.Path(fp)
                fn_w_ext = fp.relative_to(self.data_dir)
                fns[fn_w_ext] = _build_url(self.data_dir, fn_w_ext)
            return fns

    def _build_result_link_node(self, filename, dl_url):
        filename = str(filename)  # in case of pathlib.Path
        ast = [
            md.inline_code_ast(filename),
            md.text_ast(' | '),
            md.link_ast('download', dl_url)
        ]
        if filename.endswith('qza') or filename.endswith('qzv'):
            quoted_url = urllib.parse.quote_plus(dl_url)
            view_url = 'https://view.qiime2.org?src=%s' % (quoted_url,)
            ast.extend([md.text_ast(' | '), md.link_ast('view', view_url)])

        return ast

    def render(self, flush=False, stdout=None, stderr=None, **kwargs):
        ast = []

        output_list = []
        fns_to_url = self._save_results()
        for fn, url in fns_to_url.items():
            output_list.append(self._build_result_link_node(fn, url))

        if output_list:
            ast.append(md.list_ast(*output_list))

        if stdout:
            content = self.stdout.getvalue()
            if content != '':
                ast.append(md.code_ast('text', content, filename='stdout'))

        if stderr:
            content = self.stderr.getvalue()
            if content != '':
                ast.append(md.code_ast('text', content, filename='stderr'))

        ast.extend(self.misc_nodes)

        if flush:
            self.recorder = {}
            self.stdout.truncate(0)
            self.stdout.seek(0)
            self.stderr.truncate(0)
            self.stderr.seek(0)
            self.misc_nodes = []

        return ast

    def init_artifact(self, name, factory):
        variable = super().init_artifact(name, factory)
        return self._add_record(variable)

    def init_metadata(self, name, factory):
        variable = super().init_metadata(name, factory)
        return self._add_record(variable)

    def init_format(self, name, factory, ext=None):
        if ext is not None:
            name = '%s.%s' % (name, ext)
        variable = super().init_format(name, factory, ext=ext)

        return self._add_record(variable)

    def import_from_format(self, name, semantic_type, variable,
                           view_type=None):
        variable = super().import_from_format(
            name, semantic_type, variable, view_type=view_type)
        return self._add_record(variable)

    # no merge_metadata or view_as_metadata, we don't need download links
    # for those nodes.

    def get_metadata_column(self, name, column_name, variable):
        return super().get_metadata_column(name, column_name, variable)

    def action(self, action, input_opts, output_opts):
        variables = super().action(action, input_opts, output_opts)

        if len(variables) > self.auto_collect_size:
            plugin_name = CLIUsageVariable.to_cli_name(action.plugin_id)
            action_name = CLIUsageVariable.to_cli_name(action.action_id)
            dir_name = self.cli_use._build_output_dir_name(plugin_name,
                                                           action_name)
            output_dir = self.data_dir / dir_name
            output_dir.mkdir(exist_ok=True)
            self.cli_use._rename_outputs(variables._asdict(), str(output_dir))

        for variable in variables:
            self._add_record(variable)

        return variables

    def peek(self, variable):
        with redirected_stdio(stdout=self.stdout, stderr=self.stderr):
            result = variable.execute()

        uuid = result.uuid
        type_ = result.type
        fmt = result.format

        items = []
        for term, defn in [('UUID', uuid), ('Type', type_), ('Format', fmt)]:
            items.append([
                md.text_ast(term + ' ', style='strong'),
                md.inline_code_ast(defn)
            ])

        list_node = md.list_ast(*items)
        self.misc_nodes.append(list_node)