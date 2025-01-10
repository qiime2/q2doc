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
    def apply_options(cls, ast, **options):
        return ast


def type_to_id(semantic_type):
    id = md.clean_id(str(semantic_type))
    return f'q2-type-{id}'
