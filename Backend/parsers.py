class ParsedQuery:
    def __init__(self, s):
        self.debters = {}
        self.desc = ''
        for i, line in enumerate(s.splitlines()):
            if i == 0:
                self.amount = int(line.split()[1])
            else:
                t = " ".join(line.split())
                if t.split()[0][0] == '@':
                    self.debters[t.split()[0][1:]] = (t.split()[1] if len(t.split()) > 1 else '')
                else:
                    self.desc += line + '\n'