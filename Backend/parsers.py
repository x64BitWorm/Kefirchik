import calculations

class ParsedQuery:
    def __init__(self, s):
        text = s.text
        username = s.from_user.username
        self.debters = {}
        self.desc = ''
        for i, line in enumerate(text.splitlines()):
            if i == 0:
                total = calculations.parse_expression(line.split()[1])
                if total[1] != 0:
                    raise Exception('Использование x в сумме запрещено')
                self.amount = total[0]
            else:
                t = " ".join(line.split()).split()
                if t[0][0] == '@':
                    nicknameBorder = 0
                    for i in range(len(t)):
                        if t[i][0]!='@':
                            nicknameBorder = i
                            break
                    expression = (''.join(t[nicknameBorder:]) if t[-1][0]!='@' else '')
                    for token in t:
                        if token[0]!='@':
                            break
                        k = token[1:]
                        if k == "я" or k == "Я":
                            k = username
                        self.debters[k] = expression
                else:
                    self.desc += line + '\n'
