# semantic.py

from ast_nodes import *

class SemanticError(Exception): pass

class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}
    def add(self, name, info):
        if name in self.symbols:
            raise SemanticError(f"Multiple declaration of '{name}'")
        self.symbols[name] = info
    def get(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.get(name)
        raise SemanticError(f"Undeclared identifier '{name}'")

class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.errors = []

    def analyze(self):
        self._enter_program(self.ast)
        return self.errors

    def _enter_program(self, prog: Program):
        self.global_scope = SymbolTable()
        for f in prog.funcs:
            self.global_scope.add(f.name, {
                'type': f.rtype,
                'params': [(p.vtype, p.name) for p in f.params]
            })
        for f in prog.funcs:
            self._visit_func(f)

    def _visit_func(self, func: FuncDecl):
        prev = self.current_scope if hasattr(self, 'current_scope') else None
        self.current_scope = SymbolTable(self.global_scope)
        for p in func.params:
            self.current_scope.add(p.name, {'type': p.vtype})
        self._visit_block(func.body)
        self.current_scope = prev or self.global_scope

    def _visit_block(self, block: Block):
        saved = self.current_scope
        self.current_scope = SymbolTable(saved)
        for stmt in block.stmts:
            self._visit(stmt)
        self.current_scope = saved

    def _visit(self, node):
        fn = getattr(self, f"_visit_{node.__class__.__name__}", None)
        if fn: fn(node)

    def _visit_VarDecl(self, node: VarDecl):
        if node.init:
            t = self._eval(node.init)
            if t != node.vtype:
                self.errors.append(f"Type error: cannot assign '{t}' to '{node.vtype}'")
        self.current_scope.add(node.name, {'type': node.vtype})

    def _visit_Assign(self, node: Assign):
        info = self.current_scope.get(node.name)
        t = self._eval(node.expr)
        if t != info['type']:
            self.errors.append(f"Type error: cannot assign '{t}' to '{info['type']}'")

    def _visit_IfStmt(self, node: IfStmt):
        if self._eval(node.cond) != 'bool':
            self.errors.append("Condition in if must be bool")
        self._visit_block(node.thenb)
        if node.elseb:
            self._visit_block(node.elseb)

    def _visit_WhileStmt(self, node: WhileStmt):
        if self._eval(node.cond) != 'bool':
            self.errors.append("Condition in while must be bool")
        self._visit_block(node.body)

    def _visit_ForStmt(self, node: ForStmt):
        self._visit(node.init)
        if self._eval(node.cond) != 'bool':
            self.errors.append("Condition in for must be bool")
        self._eval(node.post)
        self._visit_block(node.body)

    def _visit_ReturnStmt(self, node: ReturnStmt):
        self._eval(node.expr)

    def _visit_PrintStmt(self, node: PrintStmt):
        self._eval(node.expr)

    def _eval(self, node):
        if isinstance(node, Literal):
            return 'int' if isinstance(node.value, int) else 'float'
        if isinstance(node, ReadExpr):
            return 'int'
        if isinstance(node, VarRef):
            return self.current_scope.get(node.name)['type']
        if isinstance(node, UnOp):
            return self._eval(node.expr)
        if isinstance(node, BinOp):
            l = self._eval(node.left); r = self._eval(node.right)
            if node.op in ('+','-','*','/','%'):
                if l == r and l in ('int','float'):
                    return l
                self.errors.append(f"Type error in '{node.op}'")
                return l
            return 'bool'
        if isinstance(node, FuncCall):
            finfo = self.global_scope.get(node.name)
            if len(node.args) != len(finfo['params']):
                self.errors.append(f"Function '{node.name}' expects {len(finfo['params'])} args")
            for arg,(ptype,_) in zip(node.args, finfo['params']):
                if self._eval(arg) != ptype:
                    self.errors.append(f"Arg type mismatch in '{node.name}'")
            return finfo['type']
        return 'int'
