import re
from collections import namedtuple

# Token structure
Token = namedtuple('Token', ['type', 'value', 'line', 'column'])

# Token specification list
_TOKEN_SPEC = [
    ('COMMENT',  r'//[^\n]*|/\*.*?\*/'),                # Single-line and multi-line comments
    ('NUMBER',   r'\d+(?:\.\d+)?'),                     # Integer or float
    ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),            # Identifier
    ('OP',       r'==|!=|<=|>=|&&|\|\||[+\-*/%<>!]'),   # Operators (multi-char first)
    ('ASSIGN',   r'='),                                 # Assignment operator
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('LBRACE',   r'\{'),
    ('RBRACE',   r'\}'),
    ('COMMA',    r','),
    ('SEMI',     r';'),
    ('COLON',    r':'),
    ('NEWLINE',  r'\n'),                                # Line break
    ('WS',       r'[ \t]+'),                            # Whitespace
]

# Reserved keywords
KEYWORDS = {
    'int', 'float', 'bool',
    'if', 'else', 'while', 'for', 'switch', 'case', 'default', 'break',
    'func', 'return', 'print', 'read'
}

class Lexer:
    def __init__(self, code):
        self.code = code
        self.regex = re.compile(
            '|'.join(f'(?P<{name}>{pattern})' for name, pattern in _TOKEN_SPEC),
            re.DOTALL | re.MULTILINE
        )
        self.line = 1
        self.column = 1

    def tokenize(self):
        for mo in self.regex.finditer(self.code):
            kind = mo.lastgroup
            lexeme = mo.group()

            # Handle newlines
            if kind == 'NEWLINE':
                self.line += 1
                self.column = 1
                continue

            # Skip whitespace and comments
            if kind in ('WS', 'COMMENT'):
                self.line += lexeme.count('\n')
                if '\n' in lexeme:
                    # Reset column after newline in comment
                    last_newline_index = lexeme.rfind('\n')
                    self.column = len(lexeme) - last_newline_index
                else:
                    self.column += len(lexeme)
                continue

            # Convert identifier to keyword if it's reserved
            if kind == 'ID' and lexeme in KEYWORDS:
                kind = lexeme.upper()

            # Yield the token
            yield Token(kind, lexeme, self.line, self.column)
            self.column += len(lexeme)
