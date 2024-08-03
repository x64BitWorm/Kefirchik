class ParsedQuery:
    def __init__(self, s):
        text = s.text
        username = s.from_user.username
        self.debters = {}
        self.desc = ''
        for i, line in enumerate(text.splitlines()):
            if i == 0:
                self.amount = float(line.split()[1])
            else:
                t = " ".join(line.split()).split()
                if t[0][0] == '@':
                    expression = (t[-1] if t[-1][0]!='@' else '')
                    for token in t:
                        if token[0]!='@':
                            break
                        k = token[1:]
                        if k == "я" or k == "Я":
                            k = username
                        self.debters[k] = expression
                else:
                    self.desc += line + '\n'
