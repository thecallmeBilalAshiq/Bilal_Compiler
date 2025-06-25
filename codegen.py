from ir import Instruction
from regalloc import RegisterAllocator

class CodeGenerator:
    def __init__(self):
        self.regalloc = RegisterAllocator()
        self.asm = []

    def generate(self, tac):
        self.regalloc.reset()

        self.asm.append('global main')
        self.asm.append('extern printf')
        self.asm.append('extern scanf')

        self.asm.append('section .data')
        self.asm.append('fmt_print: db "%d", 10, 0')
        self.asm.append('fmt_read:  db "%d", 0')

        self.asm.append('section .text')
        self.asm.append('main:')
        self.asm.append('    push rbp')
        self.asm.append('    mov rbp, rsp')

        sz = self.regalloc.stack_size()
        aligned_sz = (sz + 15) & ~15
        if aligned_sz > 0:
            self.asm.append(f'    sub rsp, {aligned_sz + 32}')
        else:
            self.asm.append('    sub rsp, 32')

        for instr in tac:
            self._emit(instr)

        self.asm.append('    mov rsp, rbp')
        self.asm.append('    pop rbp')
        self.asm.append('    ret')

        return self.asm

    def _emit(self, instr: Instruction):
        op, dest, a1, a2, lbl = instr

        if op == 'label' and lbl and lbl != 'main':
            self.asm.append(f'{lbl}:')

        elif op == 'assign':
            dst = self.regalloc.get_location(dest)
            src = self._operand(a1)

            if self._is_memory(dst) and self._is_memory(src):
                self.asm.append(f'    mov rax, {src}')
                self.asm.append(f'    mov {dst}, rax')
            else:
                self.asm.append(f'    mov {dst}, {src}')

        elif op == 'binop':
            self._handle_binop(instr)

        elif op == 'unop':
            self._handle_unop(instr)

        elif op == 'call':
            self._handle_call(instr)

        elif op == 'print':
            val = self._operand(a1)
            self.asm.append(f'    mov rcx, fmt_print')
            self.asm.append(f'    mov rdx, {val}')
            self.asm.append('    sub rsp, 32')
            self.asm.append('    call printf')
            self.asm.append('    add rsp, 32')

        elif op == 'read':
            loc = self.regalloc.get_location(dest)
            if self._is_memory(loc):
                addr = loc
            else:
                offset = self.regalloc.allocate_stack_slot(dest)
                addr = f'[rbp-{offset}]'
                self.asm.append(f'    mov {addr}, {loc}')
            self.asm.append(f'    mov rcx, fmt_read')
            self.asm.append(f'    lea rdx, {addr}')
            self.asm.append('    sub rsp, 32')
            self.asm.append('    call scanf')
            self.asm.append('    add rsp, 32')
            if not self._is_memory(loc):
                self.asm.append(f'    mov {loc}, {addr}')

        elif op == 'ret':
            self.asm.append('    xor rax, rax')

        elif op == 'ifz':
            cond = self._operand(a1)
            self.asm.append(f'    cmp {cond}, 0')
            self.asm.append(f'    je {lbl}')

        elif op == 'goto':
            self.asm.append(f'    jmp {lbl}')

        else:
            self.asm.append(f'    ; unhandled {instr}')

    def _handle_binop(self, instr):
        _, dest, a1, a2, _ = instr
        dst = self.regalloc.get_location(dest)

        parts = a2.split(' ', 1)
        operator = parts[0]
        right_operand = parts[1] if len(parts) > 1 else parts[0]

        lhs = self._operand(a1)
        rhs = self._operand(right_operand)

        if operator in ('+', '-', '*'):
            self.asm.append(f'    mov rax, {lhs}')
            self.asm.append(f'    {self._binop_map(operator)} rax, {rhs}')
            self.asm.append(f'    mov {dst}, rax')

        elif operator in ('<','<=','>','>=','==','!='):
            # Fix: if both are memory, use rbx for rhs
            if self._is_memory(lhs) and self._is_memory(rhs):
                self.asm.append(f'    mov rbx, {rhs}')
                self.asm.append(f'    cmp {lhs}, rbx')
            else:
                self.asm.append(f'    cmp {lhs}, {rhs}')
            self.asm.append(f'    {self._cmp_map(operator)} al')
            self.asm.append('    movzx rax, al')
            self.asm.append(f'    mov {dst}, rax')

        else:
            self.asm.append(f'    ; unhandled binop {operator}')

    def _handle_unop(self, instr):
        _, dest, _, a2, _ = instr
        dst = self.regalloc.get_location(dest)
        val = self._operand(a2)
        self.asm.append(f'    mov rax, {val}')
        self.asm.append('    neg rax' if a2 == '-' else '    not rax')
        self.asm.append(f'    mov {dst}, rax')

    def _handle_call(self, instr):
        _, dest, a1, a2, _ = instr
        args = a2.split(',') if a2 else []
        regs = ['rcx', 'rdx', 'r8', 'r9']

        for i, arg in enumerate(args[:4]):
            self.asm.append(f'    mov {regs[i]}, {self._operand(arg)}')
        for arg in reversed(args[4:]):
            self.asm.append(f'    push {self._operand(arg)}')

        self.asm.append('    sub rsp, 32')
        self.asm.append(f'    call {a1}')
        self.asm.append('    add rsp, 32')

        if len(args) > 4:
            self.asm.append(f'    add rsp, {8 * (len(args) - 4)}')

        if dest:
            self.asm.append(f'    mov {self.regalloc.get_location(dest)}, rax')

    def _operand(self, x):
        if x is None:
            return '0'
        if x.isdigit():
            return x
        loc = self.regalloc.get_location(x)
        return f'qword {loc}' if self._is_memory(loc) else loc

    def _is_memory(self, op):
        return '[' in op

    def _binop_map(self, op):
        return {'+': 'add', '-': 'sub', '*': 'imul'}[op]

    def _cmp_map(self, op):
        return {
            '<': 'setl', '<=': 'setle',
            '>': 'setg', '>=': 'setge',
            '==': 'sete', '!=': 'setne'
        }[op]
