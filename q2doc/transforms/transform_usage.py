from .common import Transform, ast_walk
import sys
import os
import traceback
import q2doc.myst as md




def is_usage(node):
    return node.get('data', {}).get('source') == 'describe-usage'

AUTO_COLLECT = 4

class TransformUsage(Transform):
    name = 'transform-usage'
    help = 'Render a usage example'

    def __init__(self):
        self.scope = None
        self.error = None
        self.ctx = {}
        self.drivers = []


    def init_drivers(self):
        drivers = []

        from q2doc.drivers.execution import MystExecUsage

        from q2doc.drivers.q2cli import MystCLIUsage
        drivers.append(dict(name='[Command Line]', sync='cli', driver=MystCLIUsage(self.scope, AUTO_COLLECT)))

        from q2doc.drivers.python import MystPythonUsage
        drivers.append(dict(name='[Python API]', sync='python', driver=MystPythonUsage(self.scope, AUTO_COLLECT)))

        try:
            from q2doc.drivers.galaxy import MystGalaxyUsage
            drivers.append(dict(name='[Galaxy]', sync='galaxy', driver=MystGalaxyUsage(self.scope)))
        except ModuleNotFoundError:
            pass

        from q2doc.drivers.r import MystRtifactUsage
        drivers.append(dict(name='[R API]', sync='r', driver=MystRtifactUsage(self.scope)))

        return (MystExecUsage(self.scope, AUTO_COLLECT), drivers)

    def setup_scope(self, node):
        scope = node['data'].get('scope')
        if self.scope is None and scope is None:
            raise Exception('No initial scope defined.')

        if scope is not None:
            self.scope = os.path.join('data', scope)
            os.makedirs(self.scope, exist_ok=True)

        if self.scope not in self.ctx:
            self.ctx[self.scope] = self.init_drivers()

        return self.ctx[self.scope]


    def run(self, ast):
        coroutine = ast_walk(ast)
        node = None
        while node := coroutine.send(node):
            if is_usage(node):
                source = node['value']
                tabs = []
                try:
                    exec_driver, drivers = self.setup_scope(node)
                    exec(source, exec_driver.scope)
                    result = exec_driver.render(flush=True)
                    for interface in drivers:
                        exec(source, interface['driver'].scope)
                        rendered = interface['driver'].render(flush=True)
                        if rendered is None:
                            continue
                        tabs.append(md.tabitem_ast(rendered, interface['name'],
                                                   sync=interface['sync']))
                except Exception:
                    result = [md.code_ast('python', traceback.format_exc())]


                tabset = md.tabset_ast(
                    *tabs,
                    md.tabitem_ast(node, '[View Source]', sync='raw')
                )

                node = md.block_ast([tabset, *result])

        return ast