# def ast_walk(ast, root=True):
#     ast = yield ast
#     if 'children' in ast:
#         for idx in range(len(ast['children'])):
#             ast['children'][idx] = yield from ast_walk(ast['children'][idx], root=False)
#     if root:
#         yield False



def ast_walk(ast):
    if 'children' in ast:
        for idx, child in enumerate(ast['children']):
            coroutine = ast_walk(child)
            node = None
            while node := coroutine.send(node):
                node = yield node
                ast['children'][idx] = node
    yield ast
    yield False



class Transform:
    name: str
    help: str
    stage = 'document'

    def run(self, ast):
        return ast

    @classmethod
    def as_spec(cls):
        return dict(name=cls.name, doc=cls.help, stage=cls.stage)