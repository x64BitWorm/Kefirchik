import utils
import services.calculations as calculations
import re
from models.dto.parser_dto import ParsedSpendingBody

class ParsedQuery:
    def __init__(self, text = '', from_username = ''):
        self.amount = 0
        self.debtors = {}
        self.comment = ""
        self.command = ""

        first_line_pattern = r'^/(?P<command>\w+)(?:@\w+)?\s+(?P<amount_expr>.+)\s*$'
        
        lines = utils.unify_whitespace_symbols(text).splitlines()
        if not lines:
            raise utils.BotWrongInputException("Нужно ввести сумму, должников и комментарий траты")
        
        # First line parsing (command and amount)
        first_line_match = re.match(first_line_pattern, lines[0].strip(), re.IGNORECASE)
        if not first_line_match:
            raise utils.BotWrongInputException("На первой строке нужно указать сумму")
        self.command = first_line_match.group("command").lower()
        amount_expr = first_line_match.group("amount_expr")
        
        if any(x in amount_expr for x in ('x', 'X', 'х', 'Х')):
            raise utils.BotWrongInputException('Использование x в сумме запрещено')
        else:
            try:
                total = calculations.parse_expression(amount_expr, calculations.ExpressionContext())
            except:
                raise utils.BotWrongInputException('На первой строке должна быть сумма числом - <code>/add 500</code>')
            self.amount = total[0]
        
        # Following lines parsing (debtors, debts, comments)
        spending_body = parseSpendingBody(from_username, "\n".join(lines[1:]))
        self.debtors, self.comment = spending_body.debtors, spending_body.comment

# распарсить тело траты (не первая строка, а должники и комменты)
def parseSpendingBody(from_username: str, text: str) -> ParsedSpendingBody:
    debter_pattern = r'^(?P<users>(?: *@\w+)+) *(?P<expr>.*)? *$'
    debtors: dict[str, str] = {}
    comment = ''
    for line in text.splitlines():
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
                    existing_user = utils.find_username(debtors.keys(), user)
                    if existing_user != None and debtors[existing_user] and expr:
                        expr = f'0+({debtors[existing_user]})+({expr})'
                    if existing_user != None:
                        del debtors[existing_user]
                    debtors[user] = expr
            else:
                raise utils.BotWrongInputException('Неверный формат описания траты')
        else:
            comment += line + '\n'
    comment = comment.strip()
    return ParsedSpendingBody(debtors=debtors, comment=comment)
