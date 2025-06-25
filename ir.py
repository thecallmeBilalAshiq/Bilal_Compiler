# ir.py

from ast_nodes import *
from collections import namedtuple

# A simple IR instruction representation
Instruction = namedtuple('Instruction', ['op', 'dest', 'arg1', 'arg2', 'label'])

class IRGenerator:
    def __init__(self):
        self.temp_cnt = 0
        self.label_cnt = 0
        self.code = []

    def new_temp(self):
        name = f"t{self.temp_cnt}"
        self.temp_cnt += 1
        return name

    def new_label(self, base='L'):
        name = f"{base}{self.label_cnt}"
        self.label_cnt += 1
        return name

    def generate(self, prog: Program):
        self.code = []
        self._gen_Program(prog)
        return self.code

    def _emit(self, instr):
        self.code.append(instr)

    # --- Program & Functions ---
    def _gen_Program(self, node: Program):
        for f in node.funcs:
            self._gen_FuncDecl(f)

    def _gen_FuncDecl(self, node: FuncDecl):
        self._emit(Instruction('label', None, None, None, node.name))
        self._gen_Block(node.body)
        self._emit(Instruction('ret', None, None, None, None))

    # --- Statements ---
    def _gen_Block(self, node: Block):
        for stmt in node.stmts:
            self._gen(stmt)

    def _gen_ReturnStmt(self, node: ReturnStmt):
        val = self._gen(node.expr)
        self._emit(Instruction('ret', None, val, None, None))

    def _gen_PrintStmt(self, node: PrintStmt):
        v = self._gen(node.expr)
        self._emit(Instruction('print', None, v, None, None))

    def _gen_VarDecl(self, node: VarDecl):
        if node.init:
            v = self._gen(node.init)
            self._emit(Instruction('assign', node.name, v, None, None))

    def _gen_Assign(self, node: Assign):
        v = self._gen(node.expr)
        self._emit(Instruction('assign', node.name, v, None, None))

    def _gen_IfStmt(self, node: IfStmt):
        else_lbl = self.new_label('else')
        end_lbl  = self.new_label('ifend')
        cond = self._gen(node.cond)
        self._emit(Instruction('ifz', None, cond, None, else_lbl))
        self._gen_Block(node.thenb)
        self._emit(Instruction('goto', None, None, None, end_lbl))
        self._emit(Instruction('label', None, None, None, else_lbl))
        if node.elseb:
            self._gen_Block(node.elseb)
        self._emit(Instruction('label', None, None, None, end_lbl))

    def _gen_WhileStmt(self, node: WhileStmt):
        start = self.new_label('while')
        end   = self.new_label('wend')
        self._emit(Instruction('label', None, None, None, start))
        cond = self._gen(node.cond)
        self._emit(Instruction('ifz', None, cond, None, end))
        self._gen_Block(node.body)
        self._emit(Instruction('goto', None, None, None, start))
        self._emit(Instruction('label', None, None, None, end))

    def _gen_ForStmt(self, node: ForStmt):
        start = self.new_label('for')
        end   = self.new_label('forend')
        if node.init:
            self._gen(node.init)
        self._emit(Instruction('label', None, None, None, start))
        if node.cond:
            c = self._gen(node.cond)
            self._emit(Instruction('ifz', None, c, None, end))
        self._gen_Block(node.body)
        if node.post:
            self._gen(node.post)
        self._emit(Instruction('goto', None, None, None, start))
        self._emit(Instruction('label', None, None, None, end))

    def _gen_SwitchStmt(self, node: SwitchStmt):
        end_lbl = self.new_label('swend')
        expr = self._gen(node.expr)
        case_labels = []
        default_lbl = None

        for case in node.cases:
            lbl = self.new_label('case')
            case_labels.append((case, lbl))
            if case.value is None:
                default_lbl = lbl

        for case, lbl in case_labels:
            if case.value is not None:
                val = self._gen(case.value)
                tmp = self.new_temp()
                self._emit(Instruction('binop', tmp, expr, f'== {val}', None))
                self._emit(Instruction('ifnz', None, tmp, None, lbl))

        self._emit(Instruction('goto', None, None, None, default_lbl or end_lbl))

        for case, lbl in case_labels:
            self._emit(Instruction('label', None, None, None, lbl))
            self._gen_Block(case.body)
            self._emit(Instruction('goto', None, None, None, end_lbl))

        self._emit(Instruction('label', None, None, None, end_lbl))

    # --- Expressions & ReadStmt ---
    def _gen(self, node):
        meth = getattr(self, f"_gen_{type(node).__name__}", None)
        if meth:
            return meth(node)
        raise Exception(f"No IR gen for {type(node).__name__}")

    def _gen_BinOp(self, node: BinOp):
        l = self._gen(node.left)
        r = self._gen(node.right)
        t = self.new_temp()
        # operator and RHS in arg2, label=None
        self._emit(Instruction('binop', t, l, f'{node.op} {r}', None))
        return t

    def _gen_UnOp(self, node: UnOp):
        v = self._gen(node.expr)
        t = self.new_temp()
        self._emit(Instruction('unop', t, node.op, v, None))
        return t

    def _gen_Literal(self, node: Literal):
        return str(node.value)

    def _gen_VarRef(self, node: VarRef):
        return node.name

    def _gen_FuncCall(self, node: FuncCall):
        args = [self._gen(a) for a in node.args]
        t = self.new_temp()
        self._emit(Instruction('call', t, node.name, ','.join(args), None))
        return t

    def _gen_ReadStmt(self, node: ReadStmt):
        # read(var) → IR 'read' into var
        self._emit(Instruction('read', node.name, None, None, None))

    def _gen_ReadExpr(self, node: ReadExpr):
        t = self.new_temp()
        self._emit(Instruction('read', t, None, None, None))
        return t
