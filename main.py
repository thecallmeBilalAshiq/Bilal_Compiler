import sys
from lexer import Lexer
from parser import Parser, ParserError
from semantic import SemanticAnalyzer
from ir import IRGenerator
from optimizer import optimize
from llvm_codegen import LLVMCodeGenerator  # Make sure this file exists!

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <source_file>")
        sys.exit(1)

    # Step 1: Read source code
    with open(sys.argv[1], 'r') as f:
        src = f.read()

    # Step 2: Lexical Analysis
    tokens = list(Lexer(src).tokenize())
    print("Tokens:")
    for t in tokens:
        print(" ", t)

    # Step 3: Parsing
    try:
        ast = Parser(tokens).parse()
        print("\nParsing successful.")
    except ParserError as e:
        print(f"\nSyntax error: {e}")
        sys.exit(1)

    # Optional: Graphviz AST Output
    try:
        dot = ast.graph()
        dot.render("ast", format="pdf", view=False)
        print("AST graph written to ast.pdf")
    except Exception as e:
        print(f"Graphviz error: {e}")

    # Step 4: Semantic Analysis
    errors = SemanticAnalyzer(ast).analyze()
    if errors:
        print("\nSemantic errors:")
        for err in errors:
            print("  -", err)
        sys.exit(1)
    print("\nSemantic analysis passed.")

    # Step 5: IR Generation
    tac = IRGenerator().generate(ast)
    print("\n--- Unoptimized TAC ---")
    for ins in tac:
        print(" ", ins)

    # Step 6: Optimization
    optimized_tac = optimize(tac)
    print("\n--- Optimized TAC ---")
    for ins in optimized_tac:
        print(" ", ins)

    # Step 7: LLVM IR Generation
    llvm_ir_lines = LLVMCodeGenerator().generate(optimized_tac)
    print("\n--- LLVM-style IR ---")
    for line in llvm_ir_lines:
        print(line)

    # Step 8: Write LLVM IR to File
    with open("output.ll", "w") as f:
        f.write('\n'.join(llvm_ir_lines))
    print("\nLLVM IR written to output.ll")

    print("\n✅ Compilation successful! Run this to generate binary:")
    print("clang output.ll -o prog")

if __name__ == "__main__":
    main()
