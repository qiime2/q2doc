import re
import os
import shutil

from qiime2.plugin import model
from qiime2.plugin.model.directory_format import BoundFileCollection

from q2cli.core.usage import CLIUsageVariable
from q2galaxy.core.usage import GalaxyBaseUsage
from q2galaxy.core.templaters.helpers import signature_to_galaxy
from q2galaxy.core.templaters.common import (make_tool_name_from_id,
                                             make_tool_id)
from q2galaxy.core.util import pretty_fmt_name

from .common import _build_url
import q2doc.myst as md
from q2doc.directives.common import format_text


def _collect_files(dirfmt, data_dir):
    collections = {}
    individuals = {}
    paths = list(sorted(dirfmt.path.glob('**/*')))
    for field in dirfmt._fields:
        attr = getattr(dirfmt, field)
        if isinstance(attr, BoundFileCollection):
            matched = [
                f.relative_to(data_dir) for f in paths
                if re.match(attr.pathspec, str(f.relative_to(dirfmt.path)))]
            collections[field] = matched
        else:
            for f in paths:
                if re.match(attr.pathspec, str(f.relative_to(dirfmt.path))):
                    break
            else:
                raise Exception
            individuals[field] = f.relative_to(data_dir)
    return collections, individuals



def format_bullets(bullets):
    entries = []
    for bullet in bullets:
        if type(bullet) is tuple:
            entry, sublist = bullet
        else:
            entry, sublist = bullet, []

        if type(entry) is str:
            entry = format_text(entry)

        if sublist:
            sublist = format_bullets(sublist)
            entry.append(sublist)
        entries.append(entry)

    return md.list_ast(*entries, ordered=len(entries) > 1)


class MystGalaxyUsage(GalaxyBaseUsage):
    def __init__(self, data_dir):
        super().__init__()
        self.scope = dict(use=self)
        self.data_dir = data_dir
        self.ast = []

    def comment(self, text):
        self.ast.append(md.paragraph_ast(format_text(text)))


    def _to_cli_name(self, var):
        # Build a tmp cli-based variable, for filename templating!
        return CLIUsageVariable(
            var.name, lambda: None, var.var_type, var.use).to_interface_name()

    def _download_file(self, var):
        fn = self._to_cli_name(var)

        self.ast.append(md.definition_list_ast([
            (
                format_text('Using the ``Upload Data`` tool:'),
                format_bullets(self._file_bullets(fn, fn))
            )
        ]))


    def _file_bullets(self, history_id, filepath):
        url = _build_url(self.data_dir, filepath)
        return [
            ('On the first tab (**Regular**), press the ``Paste/Fetch`` data'
             ' button at the bottom.', [
                f'Set *"Name"* (first text-field) to: ``{history_id}``',
                f'In the larger text-area, copy-and-paste: {url}',
                '(*"Type"*, *"Genome"*, and *"Settings"* can be ignored)'
             ]),
            'Press the ``Start`` button at the bottom.'
        ]

    def _multifile_bullets(self, zipped_args):
        table = ''
        for history_id, filepath in zipped_args:
            url = _build_url(self.data_dir, filepath)
            table += f'{history_id}\t{url}\n'
        table = md.code_ast('text', table)
        bullets = [
            ('On the fourth tab (**Rule-based**):', [
                'Set *"Upload data as"* to ``Datasets``',
                'Set *"Load tabular data from"* to ``Pasted Table``',
                [md.text_ast('Paste the following contents into the large text area:'),
                 table],
                'Press the ``build`` button at the bottom.'
            ]),
            ('In the resulting UI, do the following:', [
                'Add a rule by pressing the ``+ Rules`` button and choosing'
                ' ``Add / Modify Column Definitions``.',
                ('In the sidebar:', [
                    'Press ``+Add Definition`` and select ``Name``. (This will'
                    ' choose column "A" by default. You should see a new'
                    ' annotation on the column header.)',
                    'Press ``+Add Definition`` and select ``URL``.',
                    'Change the dropdown above the button to be ``B``.'
                    ' (You should see the table headers list ``A (Name)`` and'
                    ' ``B (URL)``.)',
                    'Press the ``Apply`` button.'])
            ]),
            'Press the ``Upload`` button at the bottom right.'
        ]
        return bullets

    def _collection_bullets(self, history_id, filepaths):
        table = ''
        for filepath in filepaths:
            url = _build_url(self.data_dir, filepath)
            table += f'{filepath.relative_to(filepath.parts[0])}\t{url}\n'
        table = md.code_ast('text', table)

        bullets = [
            ('On the fourth tab (**Rule-based**):', [
                'Set *"Upload data as"* to ``Collection(s)``',
                'Set *"Load tabular data from"* to ``Pasted Table``',
                [md.text_ast('Paste the following contents into the large text area:'), table],
                'Press the ``build`` button at the bottom.'
            ]),
            ('In the resulting UI, do the following:', [
                'Add a rule by pressing the ``+ Rules`` button and choosing'
                ' ``Add / Modify Column Definitions``.',
                ('In the sidebar:', [
                    'Press ``+Add Definition`` and select'
                    ' ``List Identifier(s)``, then select column ``A``.',
                    'Press ``+Add Definition`` and select ``URL``.',
                    'Change the dropdown above the button to be ``B``.'
                    ' (You should see the table headers list'
                    ' ``A (List Identifier)`` and ``B (URL)``.)',
                    'Press the ``Apply`` button.'])
            ]),
            f'In the bottom right, set *"Name"* to be ``{history_id}``',
            'Press the ``Upload`` button at the bottom right.'
        ]
        return bullets

    def init_metadata(self, name, factory):
        var = super().init_metadata(name, factory)

        self._download_file(var)

        return var

    def init_artifact(self, name, factory):
        var = super().init_artifact(name, factory)

        self._download_file(var)

        return var

    def _save_dirfmt(self, var, fmt):
        """Save the directory format to the site's data_dir,
        returns a new directory format mounted on the saved location.
        """
        data_dir = self.data_dir
        dir_name = self._to_cli_name(var)
        save_path = os.path.join(data_dir, dir_name)
        if os.path.exists(save_path):
            shutil.rmtree(save_path)
        fmt.save(save_path)
        return fmt.__class__(save_path, mode='r')

    def init_format(self, name, factory, ext=None):
        if ext is not None:
            name = '%s.%s' % (name, ext)
        var = super().init_format(name, factory, ext=ext)

        data_dir = self.data_dir
        fmt = var.execute()

        if isinstance(fmt, model.DirectoryFormat):
            root_name = var.to_interface_name()

            var._q2galaxy_ref = {}
            dirfmt = self._save_dirfmt(var, fmt)

            collections, individuals = _collect_files(dirfmt, data_dir)

            instructions = []

            for attr_name, filepaths in collections.items():
                history_id = f'{root_name}:{attr_name}'
                var._q2galaxy_ref[attr_name] = history_id
                bullets = self._collection_bullets(history_id, filepaths)
                instructions.append(
                    (f'Steps to setup ``{history_id}``:', bullets))

            bullet_args = []
            for attr_name, filepath in individuals.items():
                history_id = f'{root_name}:{attr_name}'
                if filepath.name == getattr(dirfmt, attr_name).pathspec:
                    use_name_field = False
                else:
                    use_name_field = True
                var._q2galaxy_ref[attr_name] = (
                    history_id, use_name_field, filepath.name)
                bullet_args.append((history_id, filepath))

            if len(bullet_args) == 1:
                bullets = self._file_bullets(*bullet_args[0])
                instructions.append(
                    (f'Steps to setup ``{history_id}``:', bullets))
            elif bullet_args:
                bullets = self._multifile_bullets(bullet_args)
                instructions.append(
                    (f'Steps to setup ``{root_name}``:', bullets))


            self.ast.append(md.definition_list_ast([
                (
                    format_text('Using the ``Upload Data`` tool:'),
                    format_bullets(instructions)
                )
            ]))

        else:
            self._download_file(var)

        return var

    def import_from_format(self, name, semantic_type, variable,
                           view_type=None):
        var = super().import_from_format(name, semantic_type, variable,
                                         view_type=view_type)

        # HACK -ish
        if view_type is None or type(view_type) is str:
            view_type = variable.execute().__class__

        galaxy_fmt = pretty_fmt_name(view_type)
        instructions = [
            f'Set *"Type of data to import"* to ``{semantic_type}``',
            f'Set *"QIIME 2 file format to import from"* to ``{galaxy_fmt}``',
        ]
        info = variable.to_interface_name()
        if type(info) is dict:
            for attr, ref in variable.to_interface_name().items():
                bullets = []
                instructions.append((
                    f'For ``import_{attr}``, do the following:', bullets))

                if type(ref) is tuple:
                    history_id, use_name_field, name = ref
                    if use_name_field:
                        bullets.append(f'Set *"name"* to ``{name}``')
                    else:
                        bullets.append(f'Leave *"name"* as ``{name}``')
                    bullets.append(f'Set *"data"* to ``#: {history_id}``')
                else:
                    bullets.extend([
                        'Leave *"Select a mechanism"* as'
                        ' ``Use collection to import``',
                        f'Set *"elements"* to ``#: {ref}``',
                        'Leave *"Append an extension?"* as ``No``.'
                    ])
        else:
            instructions.append(f'Set *"data"* to ``#: {info}``')

        instructions.append('Press the ``Execute`` button.')

        self.ast.append(md.definition_list_ast([
            (
                format_text('Using the ``qiime2 tools import`` tool:'),
                format_bullets(instructions)
            )
        ]))

        self.ast.append(md.definition_list_ast([
            (
                format_text('Once completed, for the new entry in your history, use the'
                            ' ``Edit`` button to set the name as follows:'),
                [
                    md.text_ast('(Renaming is optional, but it will make any subsequent steps'
                    ' easier to complete.)'),
                    md.table_ast([
                        (md.inline_code_ast('#: qiime2 tools import [...]'),
                         md.inline_code_ast(var.to_interface_name()))
                    ], col_headers=['History Name', '"Name" to set (be sure to press [Save])'])
                ]
            )
        ]))

        return var

    def action(self, action, inputs, outputs):
        results = super().action(action, inputs, outputs)

        tool_name = make_tool_name_from_id(make_tool_id(action.plugin_id,
                                                        action.action_id))

        sig = action.get_action().signature
        mapped = inputs.map_variables(lambda v: v.to_interface_name())

        standard_cases = []
        advanced_cases = []
        for case in signature_to_galaxy(sig, mapped, data_dir=self.data_dir):
            if case.is_advanced():
                advanced_cases.append(case)
            else:
                standard_cases.append(case)

        instructions = [case.rst_instructions() for case in standard_cases]
        if advanced_cases:
            instructions.append(
                ('Expand the ``additional options`` section',
                 [case.rst_instructions() for case in advanced_cases])
            )
        instructions.append('Press the ``Execute`` button.')

        self.ast.append(md.definition_list_ast([
            (
                format_text(f'Using the ``{tool_name}`` tool:'),
                format_bullets(instructions)
            )
        ]))

        use_og_name = all(getattr(results, n).name == n for n in sig.outputs)
        if not use_og_name:
            if len(sig.outputs) > 1:
                clause = 'for each new entry in your history'
            else:
                clause = 'for the new entry in your history'

            rows = []
            for output_name, spec in sig.outputs.items():
                try:
                    var = getattr(results, output_name)
                except AttributeError:
                    continue
                ext = 'qzv' if spec.qiime_type.name == 'Visualization' else 'qza'
                history_name = f"{tool_name} [...] : {output_name}.{ext}"
                if use_og_name:
                    var._q2galaxy_ref = history_name
                else:
                    rows.append((md.inline_code_ast(f'#: {history_name}'),
                                md.inline_code_ast(var.to_interface_name())))

            self.ast.append(md.definition_list_ast([
                (
                    format_text(f'Once completed, {clause}, use the'
                                f' ``Edit`` button to set the name as follows:'),
                    [
                        md.text_ast('(Renaming is optional, but it will make any subsequent steps'
                        ' easier to complete.)'),
                        md.table_ast(rows, col_headers=['History Name', '"Name" to set (be sure to press [Save])'])
                    ]
                )
            ]))

        return results

    def render(self, flush=False, **kwargs):
        ast = self.ast
        if flush:
            self.ast = []

        return ast

