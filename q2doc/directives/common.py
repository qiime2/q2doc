import re

import q2doc.myst as md


class DirectiveHandler:
    @classmethod
    def as_spec(cls):
        return dict(name=cls.name,
                    doc=cls.__doc__,
                    arg=dict(type='string', doc=cls.arg_help),
                    options=cls.get_options())

    @classmethod
    def get_options(cls):
        return {}

    @classmethod
    def apply_options(cls, ast, node, **options):
        return ast


def type_to_id(semantic_type):
    id = md.clean_id(str(semantic_type))
    return f'q2-type-{id}'


def format_to_id(format):
    if type(format) is not str:
        format = format.__name__
    id = md.clean_id(format)
    return f'q2-format-{id}'


def action_to_id(action):
    return f'q2-action-{action.plugin_id.replace("_", "-")}-{action.id.replace("_", "-")}'

def plugin_to_id(plugin):
    if type(plugin) is not str:
        plugin = plugin.id.replace('_', "-")
    return f'q2-plugin-{plugin}'


regex = re.compile(r"""
  \W
  (?P<outer>                    # match inside word break
    (?P<type>`|__|\*\*|\*|_)    # capture type
      (?P<content>.*?)          # lazy match content
    (?P=type)                   # force closing type
  )
  \W
|                                           # Alternative
  (?P<url>
    https?:\/\/(?:[-a-zA-Z0-9-]{1,256}\.)+[a-z]{2,15}  # host
    (?::\d+)?                                             # port
    (?:
      \/?[-a-zA-Z0-9@:%_+~#?&/=.]*                        # path with
         [-a-zA-Z0-9@:%_+~#?&/=]                          # non-trailing punc.
    |
      \/                                                  # empty path
    )?
  )
""", re.VERBOSE)

style_map = {
    '__': 'strong',
    '**': 'strong',
    '_': 'emphasis',
    '*': 'emphasis',
    '`': 'inlineCode',
    None: 'link'
}
def format_text(text):
    ast = []
    plain_start = 0
    for match in regex.finditer(text):
        start, end = match.span('outer')
        if start == -1 and end == -1:
            start, end = match.span('url')
        assert start >= 0 and end >= 0

        ast.append(md.text_ast(text[plain_start:start]))
        plain_start = end

        style = style_map[match.group('type')]
        content = match.group('content')
        if content is None:
            content = match.group('url')
            if content is None:
                continue

        if style == 'inlineCode':
            ast.append(md.inline_code_ast(content))
        elif style == 'link':
            ast.append(md.link_ast(content, content))
        else:
            ast.append(md.text_ast(content, style=style))

    if plain_start < len(text):
        ast.append(md.text_ast(text[plain_start:]))

    return ast


def format_paragraphs(text):
    ast = []
    paragraphs = text.split('\n\n')
    for para in paragraphs:
        if para.strip() != '':
          ast.append(md.paragraph_ast(format_text(para)))
    return ast


def format_citations(id, citations):
    entries = []
    first = True
    for idx in range(len(citations)):
        if not first:
            entries.append(md.text_ast('; '))
        first = False

        key = f'{id}-{idx}'
        entries.append(md.cite_ast(key))
    return entries
