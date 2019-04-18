class QTable:
    attrList = [
        'street',
        'ehs',
        'pot',
        'action',
    ]

    def __init__(self):
        self.table = {}

    def contains(self, attrs):
        tmp = self.table
        for attr in self.attrList:
            if not attrs[attr] in tmp:
                return False
            tmp = tmp[attrs[attr]]
        return True

    def get(self, attrs):
        tmp = self.table
        for attr in self.attrList:
            if not attrs[attr] in tmp:
                return [None, None]
            tmp = tmp[attrs[attr]]
        return tmp

    def set(self, attrs, val):
        prev = None
        key = None
        tmp = self.table
        for attr in self.attrList:
            if not attrs[attr] in tmp:
                tmp[attrs[attr]] = {}
            prev = tmp
            key = attrs[attr]
            tmp = tmp[attrs[attr]]
        prev[key] = val

    def recursiveTrace(self, n, item):
        if n == 0:
            return [", ".join(list(map(str, item)))]
        keys = []
        for i in item:
            tmp = self.recursiveTrace(n - 1, item[i])
            for j in tmp:
                keys.append(str(i) + ", " + j)
        return keys

    def aslist(self):
        # return str(self.table)
        return self.recursiveTrace(len(self.attrList), self.table)

    def format(self):
        return "\n".join(self.aslist())

    def __str__(self):
        return self.aslist()

    def loadfile(self, filename):
        f = open(filename)
        for line in f:
            street, ehs, pot, action, q, n = line.strip().split(", ")
            print("read: ", street, ehs, pot, action, q, n)
            self.set({
                'street': street,
                'ehs': ehs,
                'pot': pot,
                'action': action
            }, [q, n])

    def writefile(self, filename):
        f = open(filename, 'w')
        f.write(self.format())
        f.close()

qt = QTable()
qt.set({
    'street': 'flop',
    'ehs': '0.54',
    'pot': '3',
    'action': 'call'
}, [3, 12])

print(qt.aslist())