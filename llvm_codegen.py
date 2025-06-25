class LLVMCodeGenerator:
    def __init__(self):
        self.lines = []
        self.regcnt = 0
        self.current_block = "entry"

    def _reg(self):
        r = f"%r{self.regcnt}"
        self.regcnt += 1
        return r

    def _emit(self, line):
        self.lines.append(line)

    def generate(self, ir):
        self.regcnt = 0
        self.lines = []
        self.current_block = "entry"

        # --- prologue ---
        self._emit('declare i32 @printf(i8*, ...)')
        self._emit('declare i32 @scanf(i8*, ...)')
        self._emit('@.in = constant [3 x i8] c"%d\\00"')
        self._emit('@.out = constant [4 x i8] c"%d\\0A\\00"')
        self._emit('')
        self._emit('define i32 @main() {')
        self._emit('entry:')

        # --- walk the IR ---
        for op, dest, a1, a2, label in ir:
            if op == 'label':
                if label != 'main':
                    if self.current_block != label:
                        self._emit(f'  br label %{label}')
                    self._emit(f'{label}:')
                    self.current_block = label
                continue

            if op == 'read':
                self._handle_read(dest)
            elif op == 'assign':
                self._handle_assign(dest, a1)
            elif op == 'binop':
                self._handle_binop(dest, a1, a2)
            elif op == 'print':
                self._handle_print(a1)
            elif op == 'ifz':
                self._handle_ifz(a1, label)
            elif op == 'goto':
                self._handle_goto(label)
            elif op == 'ret':
                self._handle_ret()

        # --- epilogue ---
        if self.current_block != "entry":
            self._emit('  ret i32 0')
        self._emit('}')
        return self.lines

    # --- Handlers ---

    def _handle_read(self, dest):
        # scanf into local alloca
        self._emit(f'  %{dest} = alloca i32')
        self._emit(
            f'  call i32 (i8*, ...) @scanf(i8* getelementptr ([3 x i8], [3 x i8]* @.in, i32 0, i32 0), i32* %{dest})'
        )

    def _handle_assign(self, dest, value):
        # dest = value
        # allocate dest
        self._emit(f'  %{dest} = alloca i32')

        # figure out if value is a pointer (another alloca)
        if value.isidentifier():
            src_ptr = f'%{value}'
            tmp = self._reg()
            self._emit(f'  {tmp} = load i32, i32* {src_ptr}')
            store_val = tmp
        else:
            # immediate constant
            store_val = value

        self._emit(f'  store i32 {store_val}, i32* %{dest}')

    def _handle_binop(self, dest, left, right_expr):
        op_symbol, right = right_expr.split(' ', 1)
        if op_symbol in ['+', '-', '*']:
            self._emit_arithmetic(dest, op_symbol, left, right)
        else:
            self._emit_comparison(dest, op_symbol, left, right)

    def _emit_arithmetic(self, dest, op, left, right):
        instr_map = {'+':'add', '-':'sub', '*':'mul'}

        # helper to get "%x" from "x"
        def ptr_tok(x): return x if x.startswith('%') else f'%{x}'

        # load left operand
        lptr = ptr_tok(left)
        lval = self._reg()
        self._emit(f'  {lval} = load i32, i32* {lptr}')

        # load right operand
        rptr = ptr_tok(right)
        rval = self._reg()
        self._emit(f'  {rval} = load i32, i32* {rptr}')

        # do the add/sub/mul
        tmp = self._reg()
        self._emit(f'  {tmp} = {instr_map[op]} i32 {lval}, {rval}')

        # store into dest
        self._emit(f'  %{dest} = alloca i32')
        self._emit(f'  store i32 {tmp}, i32* %{dest}')

    def _emit_comparison(self, dest, op, left, right):
        cmp_map = {'<':'slt','<=':'sle','>':'sgt','>=':'sge','==':'eq','!=':'ne'}

        lv = f'%{left}' if left.isidentifier() else left
        rv = f'%{right}' if right.isidentifier() else right

        t1 = self._reg()
        self._emit(f'  {t1} = icmp {cmp_map[op]} i32 {lv}, {rv}')
        t2 = self._reg()
        self._emit(f'  {t2} = zext i1 {t1} to i32')
        self._emit(f'  %{dest} = alloca i32')
        self._emit(f'  store i32 {t2}, i32* %{dest}')

    def _handle_print(self, value):
        ptr = value if value.startswith('%') else f'%{value}'
        tmp = self._reg()
        self._emit(f'  {tmp} = load i32, i32* {ptr}')
        self._emit(
            f'  call i32 (i8*, ...) @printf(i8* getelementptr ([4 x i8], [4 x i8]* @.out, i32 0, i32 0), i32 {tmp})'
        )

    def _handle_ifz(self, cond, label):
        self._emit(f'  %cond = load i32, i32* %{cond}')
        self._emit(f'  %check = icmp eq i32 %cond, 0')
        nextb = f'next{self.regcnt}'
        self.regcnt += 1
        self._emit(f'  br i1 %check, label %{label}, label %{nextb}')
        self._emit(f'{nextb}:')
        self.current_block = nextb

    def _handle_goto(self, label):
        self._emit(f'  br label %{label}')
        self.current_block = None

    def _handle_ret(self):
        self._emit('  ret i32 0')
