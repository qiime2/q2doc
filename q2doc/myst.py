import re


def clean_id(id):
    id = id.lower()
    id = re.sub(r'[^a-z0-9]', '-', id)
    id = re.sub(r'--+', '-', id)
    id = re.sub(r'-$|^-', '', id)
    return id


def directive_md(name, arg, body_='', visible_=True, **options):
    fence = '```'
    if visible_:
        fence = ':::'
    opts = '\n'.join(f':{key}: {value}' for key, value in options.items())
    if opts:
        opts += '\n'
        if body_:
            opts += '\n'
    if body_:
        body_ += '\n'
    return f'{fence}{{{name}}} {arg}\n{opts}{body_}{fence}\n\n'


def frontmatter_yml(**kwargs):
    fence = '---'
    result = []
    for key, value in kwargs.items():
        result.append(f'{key}: {value}')
    frontmatter = '\n'.join(result)
    return f"{fence}\n{frontmatter}\n{fence}\n\n"


def inline_code_ast(text):
    return dict(type='inlineCode', value=text)


def text_ast(text, style=None):
    if type(text) is str:
        text = dict(type='text', value=text)

    if style is not None:
        return dict(type=style, children=[text])
    else:
        return text


def span_ast(children, css):
    if type(children) is str:
        children = [text_ast(children)]
    elif type(children) is dict:
        children = [children]
    return dict(type='span', style=css, children=children)

def div_ast(children, classes):
    if type(children) is str:
        children = [text_ast(children)]
    elif type(children) is dict:
        children = [children]
    return {
        'type': 'div',
        'class': classes,
        'children': children
    }


def paragraph_ast(children):
    children_ast = []
    for child in children:
        if type(child) is str:
            child = text_ast(child)
        children_ast.append(child)

    return dict(type='paragraph', children=children_ast)


def heading_ast(depth, text, id=True, implicit=False):
    extra = {}
    if implicit:
        extra['implicit'] = True
    if id is False:
        extra['implicit'] = True
        extra['identifier'] = clean_id(text)
    elif id is True:
        extra['identifier'] = clean_id(text)
    else:
        extra['identifier'] = id

    if type(text) is str:
        text = [text_ast(text)]
    elif type(text) is dict:
        text = [text]

    return dict(type='heading', depth=depth,
                label=text, children=text, **extra)


def target_ast(label):
    return dict(type='mystTarget', label=label)


def cross_reference_ast(text, id):
    if type(text) is str:
        text = [text_ast(text)]
    elif type(text) is dict:
        text = [text]
    return dict(type='crossReference', identifier=id, children=text)


def link_ast(text, url):
    return dict(type='link', url=url, children=[text_ast(text)])


def list_ast(*children, ordered=False):
    children = [dict(type='listItem', children=c) for c in children]
    return dict(type='list', ordered=ordered, children=children)


def definition_list_ast(items):
    children_ast = []
    for key, value in items:
        if type(key) is str:
            key = [text_ast(key)]
        elif type(key) is dict:
            key = [key]

        if type(value) is str:
            value = [text_ast(value)]
        elif type(value) is dict:
            value = [value]
        elif value is None:
            value = [text_ast('')]

        children_ast.append(dict(type='definitionTerm', children=key))
        if value is not None:
            children_ast.append(dict(type='definitionDescription',
                                     children=value))

    return dict(type='definitionList', children=children_ast)


def kv_list_ast(dictionary):
    return definition_list_ast([
        (kv_header_ast(key, value), None)
        for key, value in dictionary.items()
    ])

def kv_header_ast(key, value):
    return [text_ast(key, style='strong'), text_ast(': '), text_ast(value)]



def table_ast(rows, row_headers=None, col_headers=None):
    table_ast = []
    if col_headers is not None:
        header_ast = []
        if row_headers:
            header_ast.append(dict(type='tableCell', children=[]))
        for col in col_headers:
            header_ast.append(dict(type='tableCell', header=True,
                                   children=[text_ast(col)]))
        table_ast.append(dict(type='tableRow', children=header_ast))

    if row_headers is None:
        row_headers = [None] * len(rows)

    for header, row in zip(row_headers, rows):
        row_ast = []
        if header is not None:
            row_ast.append(dict(type='tableCell', header=True, align='right',
                                children=[text_ast(header)]))
        for col in row:
            row_ast.append(dict(type='tableCell', children=[text_ast(col)]))

        table_ast.append(dict(type='tableRow', children=row_ast))

    return dict(type='table', children=table_ast)


def admonition_ast(text, title, kind):
    if type(text) is str:
        text = [text_ast(text)]
    elif type(text) is dict:
        text = [text]

    if type(title) is str:
        title = [text_ast(title)]
    elif type(title) is dict:
        title = [title]
    title = [dict(type='admonitionTitle', children=title)]
    return dict(type='admonition', kind=kind, children=title+text)


def cite_ast(key):
    return dict(type='cite', identifier=key, label=key)


def code_ast(lang, value, filename=None):
    ast = dict(type='code', lang=lang, value=value)
    if filename is not None:
        ast['filename'] = filename
    return ast


def directive_ast(name, args=None, value=None, children=None):
    result =  dict(type='mystDirective', name=name)
    if args:
        result['args'] = args
    if value:
        result['value'] = value
    if children:
        result['children'] = children
    return result


def tabset_ast(*tabs):
    return dict(type='tabSet', children=tabs)


def tabitem_ast(content, title, sync=None):
    if type(content) is dict:
        content = [content]

    ast = dict(type='tabItem', title=title, children=content)
    if sync is not None:
        ast['sync'] = sync
    return ast

def block_ast(children):
    return dict(type='block', children=children)