# parser.py

from collections import deque
from lexer import Token, Lexer
from ast_nodes import *

class ParserError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = deque(tokens)
        self.current = None
        self._advance()

    def _advance(self):
        self.current = self.tokens.popleft() if self.tokens else Token('EOF', '', -1, -1)

    def _eat(self, ttype):
        if self.current.type == ttype:
            self._advance()
        else:
            raise ParserError(f"Expected {ttype} at line {self.current.line}")

    def parse(self):
        funcs = []
        while self.current.type != 'EOF':
            funcs.append(self._func_decl())
        return Program(funcs)

    # --- Top-level function declarations ---
    def _func_decl(self):
        # return type (INT/FLOAT/BOOL)
        rtype = self.current.value
        self._eat(self.current.type)

        # name
        name = self.current.value
        self._eat('ID')

        # parameter list
        self._eat('LPAREN')
        params = []
        if self.current.type != 'RPAREN':
            params = self._param_list()
        self._eat('RPAREN')

        # body
        body = self._block()
        return FuncDecl(rtype, name, params, body)

    def _param_list(self):
        ps = []
        while True:
            ptype = self.current.value
            self._eat(self.current.type)  # INT/FLOAT/BOOL
            pname = self.current.value
            self._eat('ID')
            ps.append(VarDecl(ptype, pname))
            if self.current.type == 'COMMA':
                self._eat('COMMA')
            else:
                break
        return ps

    # --- Blocks & Statements ---
    def _block(self):
        stmts = []
        self._eat('LBRACE')
        while self.current.type != 'RBRACE':
            stmts.append(self._stmt())
        self._eat('RBRACE')
        return Block(stmts)

    def _stmt(self):
        t = self.current.type

        # Variable declaration
        if t in ('INT', 'FLOAT', 'BOOL'):
            return self._vardecl()

        # Control-flow statements
        if t == 'IF':
            return self._ifstmt()
        if t == 'WHILE':
            return self._whilestmt()
        if t == 'FOR':
            return self._forstmt()
        if t == 'SWITCH':
            return self._switchstmt()

        # Return
        if t == 'RETURN':
            self._eat('RETURN')
            expr = self._expr()
            self._eat('SEMI')
            return ReturnStmt(expr)

        # Print
        if t == 'PRINT':
            self._eat('PRINT')
            self._eat('LPAREN')
            expr = self._expr()
            self._eat('RPAREN')
            self._eat('SEMI')
            return PrintStmt(expr)

        # Read (new)
        if t == 'READ':
            self._eat('READ')
            self._eat('LPAREN')
            varname = self.current.value
            self._eat('ID')
            self._eat('RPAREN')
            self._eat('SEMI')
            return ReadStmt(varname)

        # Break
        if t == 'BREAK':
            self._eat('BREAK')
            self._eat('SEMI')
            return BreakStmt()

        # ID: either FuncCall or assignment
        if t == 'ID':
            name = self.current.value
            self._eat('ID')

            # Function call statement
            if self.current.type == 'LPAREN':
                args = self._arg_list()
                self._eat('SEMI')
                return FuncCall(name, args)

            # Assignment statement
            self._eat('ASSIGN')
            expr = self._expr()
            self._eat('SEMI')
            return Assign(name, expr)

        # Expression-statement fallback
        expr = self._expr()
        self._eat('SEMI')
        return expr

    def _vardecl(self):
        vtype = self.current.value
        self._eat(self.current.type)  # INT/FLOAT/BOOL
        name = self.current.value
        self._eat('ID')
        init = None
        if self.current.type == 'ASSIGN':
            self._eat('ASSIGN')
            init = self._expr()
        self._eat('SEMI')
        return VarDecl(vtype, name, init)

    def _vardecl_for(self):
        # like _vardecl but without consuming the trailing ';'
        vtype = self.current.value
        self._eat(self.current.type)
        name = self.current.value
        self._eat('ID')
        init = None
        if self.current.type == 'ASSIGN':
            self._eat('ASSIGN')
            init = self._expr()
        return VarDecl(vtype, name, init)

    def _ifstmt(self):
        self._eat('IF')
        self._eat('LPAREN')
        cond = self._expr()
        self._eat('RPAREN')
        thenb = self._block()
        elseb = None
        if self.current.type == 'ELSE':
            self._eat('ELSE')
            elseb = self._block()
        return IfStmt(cond, thenb, elseb)

    def _whilestmt(self):
        self._eat('WHILE')
        self._eat('LPAREN')
        cond = self._expr()
        self._eat('RPAREN')
        body = self._block()
        return WhileStmt(cond, body)

    def _forstmt(self):
        self._eat('FOR')
        self._eat('LPAREN')
        init = None
        if self.current.type in ('INT','FLOAT','BOOL'):
            init = self._vardecl_for()
        elif self.current.type == 'ID':
            name = self.current.value
            self._eat('ID')
            self._eat('ASSIGN')
            expr = self._expr()
            init = Assign(name, expr)
        self._eat('SEMI')

        cond = None
        if self.current.type != 'SEMI':
            cond = self._expr()
        self._eat('SEMI')

        post = None
        if self.current.type != 'RPAREN':
            post = self._expr()
        self._eat('RPAREN')

        body = self._block()
        return ForStmt(init, cond, post, body)

    def _switchstmt(self):
        self._eat('SWITCH')
        self._eat('LPAREN')
        expr = self._expr()
        self._eat('RPAREN')
        self._eat('LBRACE')

        cases = []
        while self.current.type in ('CASE','DEFAULT'):
            if self.current.type == 'CASE':
                self._eat('CASE')
                val = self._expr()
            else:
                self._eat('DEFAULT')
                val = None
            self._eat('COLON')

            body = []
            while self.current.type not in ('CASE','DEFAULT','RBRACE'):
                if self.current.type == 'BREAK':
                    self._eat('BREAK')
                    self._eat('SEMI')
                    break
                body.append(self._stmt())
            cases.append(Case(val, Block(body)))

        self._eat('RBRACE')
        return SwitchStmt(expr, cases)

    # --- Expression parsing (with lowest-precedence assignment) ---
    def _expr(self):
        node = self._logical_or()
        if self.current.type == 'ASSIGN':
            self._eat('ASSIGN')
            rhs = self._expr()
            if not isinstance(node, VarRef):
                raise ParserError(f"Invalid assignment target at line {self.current.line}")
            return Assign(node.name, rhs)
        return node

    def _logical_or(self):
        node = self._logical_and()
        while self.current.type == 'OP' and self.current.value == '||':
            op = self.current.value
            self._eat('OP')
            node = BinOp(op, node, self._logical_and())
        return node

    def _logical_and(self):
        node = self._equality()
        while self.current.type == 'OP' and self.current.value == '&&':
            op = self.current.value
            self._eat('OP')
            node = BinOp(op, node, self._equality())
        return node

    def _equality(self):
        node = self._relational()
        while self.current.type == 'OP' and self.current.value in ('==','!='):
            op = self.current.value
            self._eat('OP')
            node = BinOp(op, node, self._relational())
        return node

    def _relational(self):
        node = self._additive()
        while self.current.type == 'OP' and self.current.value in ('<','>','<=','>='):
            op = self.current.value
            self._eat('OP')
            node = BinOp(op, node, self._additive())
        return node

    def _additive(self):
        node = self._multiplicative()
        while self.current.type == 'OP' and self.current.value in ('+','-'):
            op = self.current.value
            self._eat('OP')
            node = BinOp(op, node, self._multiplicative())
        return node

    def _multiplicative(self):
        node = self._unary()
        while self.current.type == 'OP' and self.current.value in ('*','/','%'):
            op = self.current.value
            self._eat('OP')
            node = BinOp(op, node, self._unary())
        return node

    def _unary(self):
        if self.current.type == 'OP' and self.current.value in ('-','!','++','--'):
            op = self.current.value
            self._eat('OP')
            return UnOp(op, self._primary())
        return self._primary()

    def _primary(self):
        t = self.current
        if t.type == 'NUMBER':
            val = float(t.value) if '.' in t.value else int(t.value)
            self._eat('NUMBER')
            return Literal(val)
        if t.type == 'ID':
            name = t.value
            self._eat('ID')
            if self.current.type == 'LPAREN':
                args = self._arg_list()
                return FuncCall(name, args)
            return VarRef(name)
        if t.type == 'LPAREN':
            self._eat('LPAREN')
            node = self._expr()
            self._eat('RPAREN')
            return node
        raise ParserError(f"Unexpected '{t.value}' at line {t.line}")

    def _arg_list(self):
        args = []
        self._eat('LPAREN')
        if self.current.type != 'RPAREN':
            args.append(self._expr())
            while self.current.type == 'COMMA':
                self._eat('COMMA')
                args.append(self._expr())
        self._eat('RPAREN')
        return args
