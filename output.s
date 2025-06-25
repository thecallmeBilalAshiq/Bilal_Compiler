global main
extern printf
extern scanf
section .data
fmt_print: db "%d", 10, 0
fmt_read:  db "%d", 0
section .text
main:
    push rbp
    mov rbp, rsp
    sub rsp, 32
    ; unhandled Instruction(op='label', dest=None, arg1=None, arg2=None, label='main')
    mov [rbp-8], rax
    mov rcx, fmt_read
    lea rdx, [rbp-8]
    sub rsp, 32
    call scanf
    add rsp, 32
    mov rax, [rbp-8]
    mov [rbp-16], rbx
    mov rcx, fmt_read
    lea rdx, [rbp-16]
    sub rsp, 32
    call scanf
    add rsp, 32
    mov rbx, [rbp-16]
    mov [rbp-24], rcx
    mov rcx, fmt_read
    lea rdx, [rbp-24]
    sub rsp, 32
    call scanf
    add rsp, 32
    mov rcx, [rbp-24]
    mov rbx, qword [rbp-16]
    cmp qword [rbp-8], rbx
    setg al
    movzx rax, al
    mov rdx, rax
    cmp rdx, 0
    je else0
    mov rbx, qword [rbp-24]
    cmp qword [rbp-8], rbx
    setg al
    movzx rax, al
    mov [rbp-32], rax
    cmp qword [rbp-32], 0
    je else2
    mov rax, qword [rbp-8]
    mov [rbp-40], rax
    jmp ifend3
else2:
    mov rax, qword [rbp-24]
    mov [rbp-40], rax
ifend3:
    jmp ifend1
else0:
    mov rbx, qword [rbp-24]
    cmp qword [rbp-16], rbx
    setg al
    movzx rax, al
    mov [rbp-48], rax
    cmp qword [rbp-48], 0
    je else4
    mov rax, qword [rbp-16]
    mov [rbp-40], rax
    jmp ifend5
else4:
    mov rax, qword [rbp-24]
    mov [rbp-40], rax
ifend5:
ifend1:
    mov rcx, fmt_print
    mov rdx, qword [rbp-40]
    sub rsp, 32
    call printf
    add rsp, 32
    xor rax, rax
    mov rsp, rbp
    pop rbp
    ret
