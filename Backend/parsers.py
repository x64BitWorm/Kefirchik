class ParsedQuery:
    def __init__(self, s):
        text = s.text
        username = s.from_user.username
        self.debters = {}
        self.desc = ''
        for i, line in enumerate(text.splitlines()):
            if i == 0:
                self.amount = int(line.split()[1])
            else:
                t = " ".join(line.split())
                if t.split()[0][0] == '@':
                    k = t.split()[0][1:]
                    if k == "я":
                        k = username
                    self.debters[k] = (t.split()[1] if len(t.split()) > 1 else '')
                else:
                    self.desc += line + '\n'