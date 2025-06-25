from ir import Instruction

def constant_folding(ir):
    """
    Replace binary operations on two constant literals with a single literal.
    """
    new_ir = []
    consts = {}  # map temp → constant value as string

    for instr in ir:
        if instr.op == 'binop':
            # instr.arg1 is left operand, instr.arg2 is like "+5" or "-3" etc.
            left, opb = instr.arg1, instr.arg2
            # try to split opb into operator and right operand
            for sym in ('+', '-', '*', '/', '%'):
                if opb.startswith(sym):
                    right = opb[len(sym):]
                    if left.isdigit() and right.isdigit():
                        # fold constants
                        result = str(eval(f"{left}{sym}{right}"))
                        new_ir.append(Instruction('assign', instr.dest, result, None, None))
                        consts[instr.dest] = result
                        break
            else:
                # not foldable
                new_ir.append(instr)
        else:
            # replace uses of known constants
            a1, a2 = instr.arg1, instr.arg2
            if a1 in consts:
                instr = instr._replace(arg1=consts[a1])
            if a2 in consts:
                instr = instr._replace(arg2=consts[a2])
            new_ir.append(instr)

    return new_ir

def dead_code_elimination(ir):
    """
    Remove assignments to temps that are never used.
    """
    used = set()
    # first, collect all used operands
    for instr in ir:
        if instr.arg1 and not instr.arg1.isdigit():
            used.add(instr.arg1)
        if instr.arg2 and not instr.arg2.isdigit():
            used.add(instr.arg2)

    new_ir = []
    # iterate in reverse to drop dead defs
    for instr in reversed(ir):
        if instr.dest and instr.op == 'assign' and instr.dest not in used:
            # dead definition, skip it
            continue
        new_ir.insert(0, instr)
        # after keeping it, mark *its arguments* as used
        if instr.arg1 and not instr.arg1.isdigit():
            used.add(instr.arg1)
        if instr.arg2 and not instr.arg2.isdigit():
            used.add(instr.arg2)
        if instr.dest:
            used.add(instr.dest)

    return new_ir

def strength_reduction(ir):
    """
    Replace multiplications by 2 with left shifts.
    """
    new_ir = []
    for instr in ir:
        if instr.op == 'binop' and instr.arg2 == '*2':
            # turn into unop 'shl1' (shift-left by 1)
            new_ir.append(Instruction('unop', instr.dest, 'shl1', instr.arg1, None))
        else:
            new_ir.append(instr)
    return new_ir

def common_subexpression_elimination(ir):
    """
    If the same binary operation on the same operands appears twice,
    reuse the previous temp rather than recomputing.
    """
    expr_map = {}  # (op, arg1, arg2) → dest
    new_ir = []

    for instr in ir:
        if instr.op == 'binop':
            key = (instr.op, instr.arg1, instr.arg2)
            if key in expr_map:
                prev_temp = expr_map[key]
                new_ir.append(Instruction('assign', instr.dest, prev_temp, None, None))
            else:
                expr_map[key] = instr.dest
                new_ir.append(instr)
        else:
            new_ir.append(instr)

    return new_ir

def loop_invariant_motion(ir):
    """
    Hoist loop-invariant computations out of the first for-loop encountered.
    """
    new_ir = []
    i = 0
    n = len(ir)

    while i < n:
        instr = ir[i]
        new_ir.append(instr)

        # detect a for-loop entry by a label 'forXYZ'
        if instr.op == 'label' and instr.label and instr.label.startswith('for'):
            # find matching loop-end label
            start_lbl = instr.label
            end_lbl = start_lbl + 'end'
            # locate end of loop
            j = i + 1
            while j < n and not (ir[j].op == 'label' and ir[j].label == end_lbl):
                j += 1
            if j < n:
                # get loop body instructions
                body = ir[i+1:j]
                defs = {ins.dest for ins in body if ins.dest}
                invariants = []
                # identify invariants: defs not used in their own calculation
                for ins in body:
                    if ins.dest and ins.op in ('binop','unop','assign'):
                        if (ins.arg1 not in defs) and (not ins.arg2 or ins.arg2 not in defs):
                            invariants.append(ins)
                # hoist invariants
                for inv in invariants:
                    new_ir.append(inv)
                # then re-emit body
                new_ir.extend(body)
                # skip ahead to after loop end
                i = j
        i += 1

    return new_ir

def optimize(ir):
    """
    Apply all optimizations in sequence.
    """
    ir1 = constant_folding(ir)
    ir2 = dead_code_elimination(ir1)
    ir3 = strength_reduction(ir2)
    ir4 = common_subexpression_elimination(ir3)
    ir5 = loop_invariant_motion(ir4)
    return ir5
