# ast_nodes.py

from graphviz import Digraph

class ASTNode:
    _id_iter = 0
    def __init__(self):
        self.id = ASTNode._id_iter
        ASTNode._id_iter += 1
    def children(self):
        return []
    def graph(self, dot=None):
        if dot is None:
            dot = Digraph(comment='AST')
            dot.node(str(self.id), type(self).__name__)
        for c in self.children():
            dot.node(str(c.id), type(c).__name__)
            dot.edge(str(self.id), str(c.id))
            c.graph(dot)
        return dot

class Program(ASTNode):
    def __init__(self, funcs): super().__init__(); self.funcs = funcs
    def children(self): return self.funcs

class FuncDecl(ASTNode):
    def __init__(self, rtype, name, params, body):
        super().__init__()
        self.rtype, self.name, self.params, self.body = rtype, name, params, body
    def children(self): return self.params + [self.body]

class VarDecl(ASTNode):
    def __init__(self, vtype, name, init=None):
        super().__init__()
        self.vtype, self.name, self.init = vtype, name, init
    def children(self): return [self.init] if self.init else []

class Block(ASTNode):
    def __init__(self, stmts): super().__init__(); self.stmts = stmts
    def children(self): return self.stmts

class IfStmt(ASTNode):
    def __init__(self, cond, thenb, elseb=None):
        super().__init__()
        self.cond, self.thenb, self.elseb = cond, thenb, elseb
    def children(self):
        out = [self.cond, self.thenb]
        if self.elseb: out.append(self.elseb)
        return out

class WhileStmt(ASTNode):
    def __init__(self, cond, body): super().__init__(); self.cond, self.body = cond, body
    def children(self): return [self.cond, self.body]

class ForStmt(ASTNode):
    def __init__(self, init, cond, post, body):
        super().__init__()
        self.init, self.cond, self.post, self.body = init, cond, post, body
    def children(self): return [self.init, self.cond, self.post, self.body]

class SwitchStmt(ASTNode):
    def __init__(self, expr, cases): super().__init__(); self.expr, self.cases = expr, cases
    def children(self): return [self.expr] + self.cases

class Case(ASTNode):
    def __init__(self, value, body): super().__init__(); self.value, self.body = value, body
    def children(self):
        lst = [self.body]
        if self.value is not None: lst.insert(0, self.value)
        return lst

class BreakStmt(ASTNode): pass

class ReturnStmt(ASTNode):
    def __init__(self, expr): super().__init__(); self.expr = expr
    def children(self): return [self.expr]

class PrintStmt(ASTNode):
    def __init__(self, expr): super().__init__(); self.expr = expr
    def children(self): return [self.expr]

# === New AST node for read(a); ===
class ReadStmt(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name

class ReadExpr(ASTNode): pass

class Assign(ASTNode):
    def __init__(self, name, expr): super().__init__(); self.name, self.expr = name, expr
    def children(self): return [self.expr]

class BinOp(ASTNode):
    def __init__(self, op, left, right): super().__init__(); self.op, self.left, self.right = op, left, right
    def children(self): return [self.left, self.right]

class UnOp(ASTNode):
    def __init__(self, op, expr): super().__init__(); self.op, self.expr = op, expr
    def children(self): return [self.expr]

class Literal(ASTNode):
    def __init__(self, value): super().__init__(); self.value = value

class VarRef(ASTNode):
    def __init__(self, name): super().__init__(); self.name = name

class FuncCall(ASTNode):
    def __init__(self, name, args): super().__init__(); self.name, self.args = name, args
    def children(self): return self.args
