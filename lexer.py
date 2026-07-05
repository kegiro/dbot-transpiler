import re

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line}, col={self.column})"

class LexerError(Exception):
    def __init__(self, message, line, column):
        super().__init__(f"Lexer Error at line {line}, column {column}: {message}")
        self.line = line
        self.column = column

class Lexer:
    KEYWORDS = {
        "bot": "BOT",
        "command": "COMMAND",
        "on": "ON",
        "button": "BUTTON",
        "reply": "REPLY",
        "attach": "ATTACH",
        "let": "LET",
        "create": "CREATE",
        "channel": "CHANNEL",
        "embed": "EMBED",
        "admin": "ADMIN",
        "true": "TRUE",
        "false": "FALSE",
        "if": "IF",
        "repeat": "REPEAT",
        "times": "TIMES",
        "function": "FUNCTION"
    }

    def __init__(self, source_code):
        self.source = source_code
        self.tokens = []

    def check_and_strip_escape_hatch(self, line):
        # Scan character by character to find the first unquoted '$'
        in_double_quote = False
        in_single_quote = False
        escape = False
        for i, char in enumerate(line):
            if char == '\\' and not escape:
                escape = True
                continue
            if char == '"' and not in_single_quote and not escape:
                in_double_quote = not in_double_quote
            elif char == "'" and not in_double_quote and not escape:
                in_single_quote = not in_single_quote
            elif char == '$' and not in_double_quote and not in_single_quote and not escape:
                # Found unquoted '$'
                # Strip the '$' at index i
                stripped = line[:i] + line[i+1:]
                return True, stripped
            escape = False
        return False, line

    def tokenize(self):
        lines = self.source.splitlines()
        for line_idx, raw_line in enumerate(lines):
            line_num = line_idx + 1
            
            # Convert tabs to spaces for consistency
            expanded_line = raw_line.replace('\t', '    ')
            
            # Strip leading/trailing space for checking empty lines and comments
            stripped = expanded_line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                # Ignore empty lines and comments
                continue

            # Calculate leading indentation (though not semantic anymore, helps with column tracking)
            indent = len(expanded_line) - len(expanded_line.lstrip())
            content = expanded_line[indent:]
            start_col = indent

            # Check if this line triggers the escape hatch
            is_escape, escape_content = self.check_and_strip_escape_hatch(content)
            if is_escape:
                # Emit RAW_JS token with the remaining text
                self.tokens.append(Token("RAW_JS", escape_content, line_num, start_col))
                continue

            # Regular tokenization of the line content
            col = start_col
            i = 0
            n = len(content)

            while i < n:
                char = content[i]

                # Skip whitespace
                if char.isspace():
                    i += 1
                    col += 1
                    continue

                # String Literal (double or single quotes)
                if char == '"' or char == "'":
                    quote_char = char
                    val = ""
                    start_i = i
                    i += 1  # Skip opening quote
                    col += 1
                    escaped = False
                    while i < n:
                        c = content[i]
                        if escaped:
                            val += c
                            escaped = False
                        elif c == '\\':
                            escaped = True
                        elif c == quote_char:
                            break
                        else:
                            val += c
                        i += 1
                    if i >= n:
                        raise LexerError("Unterminated string literal", line_num, start_col + start_i)
                    i += 1  # Skip closing quote
                    col += (i - start_i)
                    self.tokens.append(Token("STRING", val, line_num, start_col + start_i))
                    continue

                # Numbers
                if char.isdigit():
                    start_i = i
                    val = ""
                    while i < n and (content[i].isdigit() or content[i] == '.'):
                        # Ensure we don't treat dot operator in variable paths (like user.name) as decimal point
                        if content[i] == '.':
                            # Lookahead to see if next character is a digit
                            if i + 1 < n and content[i+1].isdigit():
                                val += content[i]
                            else:
                                break
                        else:
                            val += content[i]
                        i += 1
                    col += (i - start_i)
                    self.tokens.append(Token("NUMBER", val, line_num, start_col + start_i))
                    continue

                # Identifiers and Keywords
                if char.isalpha() or char == '_':
                    start_i = i
                    val = ""
                    while i < n and (content[i].isalnum() or content[i] == '_'):
                        val += content[i]
                        i += 1
                    col += (i - start_i)
                    if val in self.KEYWORDS:
                        self.tokens.append(Token(self.KEYWORDS[val], val, line_num, start_col + start_i))
                    else:
                        self.tokens.append(Token("IDENTIFIER", val, line_num, start_col + start_i))
                    continue

                # Multi-character Operators
                if content[i:i+2] == "!=":
                    self.tokens.append(Token("NE", "!=", line_num, col))
                    i += 2
                    col += 2
                    continue
                if content[i:i+2] == "==":
                    self.tokens.append(Token("EQ", "==", line_num, col))
                    i += 2
                    col += 2
                    continue

                # Single-character Operators & Punctuation
                if char == '=':
                    self.tokens.append(Token("ASSIGN", "=", line_num, col))
                elif char == ':':
                    self.tokens.append(Token("COLON", ":", line_num, col))
                elif char == ';':
                    self.tokens.append(Token("SEMICOLON", ";", line_num, col))
                elif char == '.':
                    self.tokens.append(Token("DOT", ".", line_num, col))
                elif char == '/':
                    self.tokens.append(Token("SLASH", "/", line_num, col))
                elif char == '(':
                    self.tokens.append(Token("LPAREN", "(", line_num, col))
                elif char == ')':
                    self.tokens.append(Token("RPAREN", ")", line_num, col))
                elif char == '{':
                    self.tokens.append(Token("LBRACE", "{", line_num, col))
                elif char == '}':
                    self.tokens.append(Token("RBRACE", "}", line_num, col))
                elif char == ',':
                    self.tokens.append(Token("COMMA", ",", line_num, col))
                elif char == '+':
                    self.tokens.append(Token("PLUS", "+", line_num, col))
                elif char == '-':
                    self.tokens.append(Token("MINUS", "-", line_num, col))
                elif char == '*':
                    self.tokens.append(Token("MULT", "*", line_num, col))
                else:
                    raise LexerError(f"Unexpected character: {repr(char)}", line_num, col)
                
                i += 1
                col += 1

        self.tokens.append(Token("EOF", "", len(lines) + 1, 0))
        return self.tokens
