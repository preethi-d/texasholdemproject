f = open('q-table-700.txt')
o = open('gen-0-700-fixed.txt', 'w')
for i in f:
    line = i.split(", ")
    line[2] = str(round(float(line[2])/40))
    o.write(", ".join(line))