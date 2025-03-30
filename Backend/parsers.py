import calculations
import re

class ParsedQuery:
    def __init__(self, text, from_username):
        self.debtors = {}
        self.comment = ""
        self.command = ""
        first_line_pattern = r'^/(?P<command>\w+)(?:@\w+)?\s+(?P<amount_expr>\S+)\s*$'
        debter_pattern = r'^(?P<users>(?: *@\w+)+) *(?P<expr>\S*) *$'
        
        lines = text.splitlines()
        if not lines:
            raise Exception("Empty message")
        
        # First line parsing (command and amount)
        first_line_match = re.match(first_line_pattern, lines[0].strip(), re.IGNORECASE)
        if not first_line_match:
            raise Exception("Invalid command format in first line")
        self.command = first_line_match.group("command").lower()
        amount_expr = first_line_match.group("amount_expr")
        
        if any(x in amount_expr for x in ('x', 'X', 'х', 'Х')):
            raise Exception('Использование x в сумме запрещено')
        else:
            total = calculations.parse_expression(amount_expr)
            self.amount = total[0]
        
        # Following lines parsing (debtors, debts, comments)
        for line in lines[1:]:
            if not line:
                continue
            if line.startswith('@'):
                match = re.match(debter_pattern, line)
                if match:
                    users_part = match.group("users")
                    expr = match.group("expr")
                    for user in re.findall(r'@(\w+)', users_part):
                        if user in {"я", "Я"}:
                            user = from_username
                        self.debtors[user] = expr
                else:
                    raise Exception('Неверный формат описания траты')
            else:
                self.comment += line + '\n'
        self.comment = self.comment.strip()
