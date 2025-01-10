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


def paragraph_ast(*children):
    children_ast = []
    for child in children:
        if type(child) is str:
            child = text_ast(child)
        children_ast.append(child)

    return dict(type='paragraph', children=children_ast)


def heading_ast(depth, text, id=True):
    extra = {}
    if id is False:
        pass
    elif id is True:
        extra['identifier'] = clean_id(text)
    else:
        extra['identifier'] = id
    return dict(type='heading', depth=depth,
                label=text, children=[text_ast(text)],
                **extra)


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

        children_ast.append(dict(type='definitionTerm', children=key))
        children_ast.append(dict(type='definitionDescription', children=value))

    return dict(type='definitionList', children=children_ast)