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


def text_ast(text):
    return dict(type='text', value=text)


def paragraph_ast(*children):
    children_ast = []
    for child in children:
        if type(child) is str:
            child = text_ast(child)
        children_ast.append(child)

    return dict(type='paragraph', children=children_ast)


def heading_ast(text, id=None):
    return dict(type='heading', depth=1,
                label=text, identifier=id if id else text,
                children=[text_ast(text)])