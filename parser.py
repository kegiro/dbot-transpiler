class ASTNode:
    pass

class ProgramNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class BotBlockNode(ASTNode):
    def __init__(self, properties):
        self.properties = properties  # dict mapping prop to expr

class CommandBlockNode(ASTNode):
    def __init__(self, command_name, body, is_admin=False, args=None):
        self.command_name = command_name
        self.body = body
        self.is_admin = is_admin
        self.args = args or []

class ButtonClickBlockNode(ASTNode):
    def __init__(self, custom_id, body):
        self.custom_id = custom_id
        self.body = body

class FunctionBlockNode(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class IfBlockNode(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class RepeatBlockNode(ASTNode):
    def __init__(self, times, body):
        self.times = times
        self.body = body

class CreateChannelBlockNode(ASTNode):
    def __init__(self, properties):
        self.properties = properties  # dict mapping name to expr

class EmbedNode(ASTNode):
    def __init__(self, properties):
        self.properties = properties  # dict mapping name to expr

class LetDeclarationNode(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class AssignmentNode(ASTNode):
    def __init__(self, target, value):
        self.target = target  # IdentifierPathNode
        self.value = value

class ReplyNode(ASTNode):
    def __init__(self, message):
        self.message = message
        self.buttons = []

class AttachButtonNode(ASTNode):
    def __init__(self, label, custom_id):
        self.label = label
        self.custom_id = custom_id

class RawJSNode(ASTNode):
    def __init__(self, code):
        self.code = code

class FunctionCallNode(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class LiteralNode(ASTNode):
    def __init__(self, value):
        self.value = value

class IdentifierPathNode(ASTNode):
    def __init__(self, path):
        self.path = path  # list of strings e.g. ['user', 'name']

class BinaryExpr(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def check(self, type_):
        tok = self.peek()
        return tok is not None and tok.type == type_

    def match(self, type_):
        if self.check(type_):
            self.pos += 1
            return self.tokens[self.pos - 1]
        return None

    def consume(self, type_):
        tok = self.match(type_)
        if tok is None:
            actual = self.peek()
            actual_str = actual.type if actual else "EOF"
            line = actual.line if actual else "EOF"
            col = actual.column if actual else "EOF"
            raise SyntaxError(f"Expected token of type {type_}, got {actual_str} at line {line}, column {col}")
        return tok

    def consume_identifier_like(self):
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Expected identifier or keyword, got EOF")
        
        is_keyword = tok.type in ("BOT", "COMMAND", "ON", "BUTTON", "REPLY", "ATTACH", "LET", "CREATE", "CHANNEL", "EMBED", "ADMIN", "TRUE", "FALSE", "IF", "REPEAT", "TIMES", "FUNCTION")
        if tok.type == "IDENTIFIER" or is_keyword:
            self.pos += 1
            return tok
        raise SyntaxError(f"Expected identifier or keyword, got token {tok.type} at line {tok.line}, column {tok.column}")

    def parse(self):
        statements = []
        while not self.check("EOF"):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return ProgramNode(statements)

    def parse_braced_block(self):
        self.consume("LBRACE")
        statements = []
        while not self.check("RBRACE") and not self.check("EOF"):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        self.consume("RBRACE")
        return statements

    def parse_statement(self):
        # Skip semicolons
        while self.match("SEMICOLON"):
            pass

        if self.check("EOF"):
            return None

        # Check for escape hatch RAW_JS
        if self.check("RAW_JS"):
            tok = self.consume("RAW_JS")
            return RawJSNode(tok.value)

        # Bot block
        if self.check("BOT"):
            self.consume("BOT")
            self.consume("LBRACE")
            properties = {}
            while not self.check("RBRACE") and not self.check("EOF"):
                prop_name = self.consume("IDENTIFIER").value
                self.consume("COLON")
                prop_val = self.parse_expression()
                properties[prop_name] = prop_val
                self.match("COMMA")
            self.consume("RBRACE")
            return BotBlockNode(properties)

        # Command block
        if self.check("COMMAND"):
            self.consume("COMMAND")
            self.match("SLASH")  # Optional slash
            
            parts = [self.consume_identifier_like().value]
            while self.match("MINUS"):
                parts.append("-")
                parts.append(self.consume_identifier_like().value)
            command_name = "".join(parts)
            
            args = []
            is_admin = False
            while not self.check("LBRACE") and not self.check("EOF"):
                tok = self.peek()
                if tok.type == "ADMIN" or tok.value == "admin":
                    self.pos += 1
                    is_admin = True
                else:
                    args.append(tok.value)
                    self.pos += 1
                    
            body = self.parse_braced_block()
            return CommandBlockNode(command_name, body, is_admin, args)

        # Event Handler: on button
        if self.check("ON"):
            self.consume("ON")
            self.consume("BUTTON")
            self.consume("LPAREN")
            button_id_expr = self.parse_expression()
            self.consume("RPAREN")
            body = self.parse_braced_block()
            if isinstance(button_id_expr, LiteralNode):
                button_id = button_id_expr.value
            elif isinstance(button_id_expr, IdentifierPathNode):
                button_id = ".".join(button_id_expr.path)
            else:
                button_id = str(button_id_expr)
            return ButtonClickBlockNode(button_id, body)

        # If block
        if self.check("IF"):
            self.consume("IF")
            has_paren = self.match("LPAREN") is not None
            cond = self.parse_expression()
            if has_paren:
                self.consume("RPAREN")
            body = self.parse_braced_block()
            return IfBlockNode(cond, body)

        # Repeat block
        if self.check("REPEAT"):
            self.consume("REPEAT")
            times = self.parse_expression()
            self.consume("TIMES")
            body = self.parse_braced_block()
            return RepeatBlockNode(times, body)

        # Create channel
        if self.check("CREATE"):
            self.consume("CREATE")
            self.consume("CHANNEL")
            self.consume("LBRACE")
            properties = {}
            while not self.check("RBRACE") and not self.check("EOF"):
                prop_name = self.consume("IDENTIFIER").value
                self.consume("COLON")
                prop_val = self.parse_expression()
                properties[prop_name] = prop_val
                self.match("COMMA")
            self.consume("RBRACE")
            return CreateChannelBlockNode(properties)

        # Embed block
        if self.check("EMBED"):
            self.consume("EMBED")
            self.consume("LBRACE")
            properties = {}
            while not self.check("RBRACE") and not self.check("EOF"):
                prop_name = self.consume("IDENTIFIER").value
                self.consume("COLON")
                prop_val = self.parse_expression()
                properties[prop_name] = prop_val
                self.match("COMMA")
            self.consume("RBRACE")
            return EmbedNode(properties)

        # Reusable Routines (Functions)
        if self.check("FUNCTION"):
            self.consume("FUNCTION")
            name = self.consume("IDENTIFIER").value
            self.consume("LPAREN")
            params = []
            if not self.check("RPAREN"):
                params.append(self.consume("IDENTIFIER").value)
                while self.match("COMMA"):
                    params.append(self.consume("IDENTIFIER").value)
            self.consume("RPAREN")
            body = self.parse_braced_block()
            return FunctionBlockNode(name, params, body)

        # Reply: reply "<text>"
        if self.check("REPLY"):
            self.consume("REPLY")
            msg_expr = self.parse_expression()
            node = ReplyNode(msg_expr)
            while self.check_attach_button():
                btn_node = self.parse_attach_button()
                node.buttons.append(btn_node)
            return node

        # Let declaration
        if self.check("LET"):
            self.consume("LET")
            name_tok = self.consume("IDENTIFIER")
            self.consume("ASSIGN")
            val_expr = self.parse_expression()
            return LetDeclarationNode(name_tok.value, val_expr)

        # Function call or assignment
        expr = self.parse_expression()
        if isinstance(expr, IdentifierPathNode) and self.match("ASSIGN"):
            val_expr = self.parse_expression()
            return AssignmentNode(expr, val_expr)
        
        return expr

    def check_attach_button(self):
        return self.check("ATTACH")

    def parse_attach_button(self):
        self.consume("ATTACH")
        self.consume("BUTTON")
        self.consume("LBRACE")
        properties = {}
        while not self.check("RBRACE") and not self.check("EOF"):
            prop_name = self.consume("IDENTIFIER").value
            self.consume("COLON")
            prop_val = self.parse_expression()
            properties[prop_name] = prop_val
            self.match("COMMA")
        self.consume("RBRACE")
        
        label_expr = properties.get("label")
        id_expr = properties.get("id")
        return AttachButtonNode(label_expr, id_expr)

    # Expression parsing with precedence
    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        expr = self.parse_additive()
        while self.peek() and self.peek().type in ("EQ", "NE"):
            op = self.match(self.peek().type).value
            right = self.parse_additive()
            expr = BinaryExpr(op, expr, right)
        return expr

    def parse_additive(self):
        expr = self.parse_multiplicative()
        while self.peek() and self.peek().type in ("PLUS", "MINUS"):
            op = self.match(self.peek().type).value
            right = self.parse_multiplicative()
            expr = BinaryExpr(op, expr, right)
        return expr

    def parse_multiplicative(self):
        expr = self.parse_primary()
        while self.peek() and self.peek().type in ("MULT", "SLASH"):
            op = self.match(self.peek().type).value
            right = self.parse_primary()
            expr = BinaryExpr(op, expr, right)
        return expr

    def parse_primary(self):
        if self.match("STRING"):
            return LiteralNode(self.tokens[self.pos-1].value)
        elif self.match("NUMBER"):
            val = self.tokens[self.pos-1].value
            return LiteralNode(float(val) if '.' in val else int(val))
        elif self.match("TRUE"):
            return LiteralNode(True)
        elif self.match("FALSE"):
            return LiteralNode(False)
        elif self.match("LPAREN"):
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr
        elif self.match("IDENTIFIER"):
            first_name = self.tokens[self.pos-1].value
            path = [first_name]
            while self.match("DOT"):
                path.append(self.consume_identifier_like().value)
            
            if self.match("LPAREN"):
                args = []
                if not self.check("RPAREN"):
                    args.append(self.parse_expression())
                    while self.match("COMMA"):
                        args.append(self.parse_expression())
                self.consume("RPAREN")
                return FunctionCallNode(".".join(path), args)
            return IdentifierPathNode(path)
        else:
            raise SyntaxError(f"Unexpected token in expression: {self.peek()}")
