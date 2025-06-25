from ir import Instruction

class LLVMGenerator:
    def __init__(self):
        self.lines = []
        self.current_func = None
        self.block_counter = 0  # for generating unique next labels

    def generate(self, ir):
        self.lines = []
        self.current_func = None
        self.block_counter = 0

        for instr in ir:
            self._emit(instr)

        if self.current_func:
            self.lines.append("}")

        return "\n".join(self.lines)

    def _emit(self, instr: Instruction):
        op, dest, a1, a2, lbl = instr

        # --- Functions ---
        if op == 'label' and lbl and lbl.isidentifier() and lbl[0].isalpha():
            if self.current_func:
                self.lines.append("}")
            self.current_func = lbl
            self.lines.append(f"define i32 @{lbl}() "+"{")
            self.lines.append("entry:")

        # --- Basic Block Labels ---
        elif op == 'label':
            self.lines.append(f"{lbl}:")

        # --- Assignment ---
        elif op == 'assign':
            rhs = self._operand(a1)
            self.lines.append(f"  %{dest} = add i32 {rhs}, 0")

        # --- Binary Operations ---
        elif op == 'binop':
            if a2 in ['+', '-', '*', '/', '%']:
                llvm_op = {'+':'add', '-':'sub', '*':'mul', '/':'sdiv', '%':'srem'}[a2]
                self.lines.append(f"  %{dest} = {llvm_op} i32 {self._operand(a1)}, {self._operand(dest)}")
            elif a2 in ['==', '!=', '<', '<=', '>', '>=']:
                llvm_cmp = {'==':'eq', '!=':'ne', '<':'slt', '<=':'sle', '>':'sgt', '>=':'sge'}[a2]
                # Perform the comparison
                self.lines.append(f"  %{dest} = icmp {llvm_cmp} i32 {self._operand(a1)}, {self._operand(dest)}")
                # Use a new temporary variable for the extended comparison result
                temp_cmp = f"cmp{self.block_counter}"
                self.block_counter += 1
                self.lines.append(f"  %{temp_cmp} = zext i1 %{dest} to i32")
                # Use the extended result for branching (if needed)
                self.lines.append(f"  %{dest} = %{temp_cmp}")  # Use the extended comparison result
            else:
                self.lines.append(f"  ; unsupported binop {instr}")

        # --- Unary Operations ---
        elif op == 'unop':
            if a1 == '-':
                self.lines.append(f"  %{dest} = sub i32 0, {self._operand(a2)}")
            elif a1 == '!':
                self.lines.append(f"  %{dest} = icmp eq i32 {self._operand(a2)}, 0")
                self.lines.append(f"  %{dest} = zext i1 %{dest} to i32")
            elif a1 == 'shl1':
                self.lines.append(f"  %{dest} = shl i32 {self._operand(a2)}, 1")
            elif a1 == 'shr1':
                self.lines.append(f"  %{dest} = ashr i32 {self._operand(a2)}, 1")
            else:
                self.lines.append(f"  ; unsupported unop {instr}")

        # --- Function Calls ---
        elif op == 'call':
            args = a2.split(',') if a2 else []
            llargs = ", ".join(f"i32 {self._operand(arg)}" for arg in args)
            self.lines.append(f"  %{dest} = call i32 @{a1}({llargs})")

        # --- Print Calls ---
        elif op == 'print':
            self.lines.append(f"  call void @print(i32 {self._operand(a1)})")

        # --- Read (input) ---
        elif op == 'read':
            self.lines.append(f"  %{dest} = call i32 @read()")

        # --- Return ---
        elif op == 'ret':
            val = self._operand(a1)
            self.lines.append(f"  ret i32 {val}")

        # --- If zero (conditional branch) ---
        elif op == 'ifz':
            cond = self._operand(a1)
            next_block = f"next{self.block_counter}"
            self.block_counter += 1
            self.lines.append(f"  %cmp{self.block_counter} = icmp eq i32 {cond}, 0")
            self.lines.append(f"  br i1 %cmp{self.block_counter}, label %{lbl}, label %{next_block}")
            self.lines.append(f"{next_block}:")

        # --- Goto (unconditional jump) ---
        elif op == 'goto':
            self.lines.append(f"  br label %{lbl}")

        else:
            self.lines.append(f"  ; unhandled {instr}")

    def _operand(self, op):
        if op is None:
            return "0"
        if op.isdigit():
            return op
        if op.startswith('t') or op.isidentifier():
            return f"%{op}"
        return op
