import matplotlib.pyplot as plt
import numpy as np
import math

# read table
files = ["../q-table-100.txt"]
# "q-table-15.txt", "q-table-20.txt", "q-table-25.txt", "q-table-30.txt", "q-table-35.txt", "q-table-40.txt", "q-table-45.txt", "q-table-50.txt", "q-table-55.txt", "q-table-60.txt", "q-table-65.txt", "q-table-70.txt", "q-table-75.txt", "q-table-80.txt", "q-table-85.txt", "q-table-90.txt", "q-table-95.txt"]
n = -1
o = 0
limit = 1200
interval = 100
base = "../q-table-{}.txt"
files = [base.format(i * interval) for i in range(1, math.floor(limit/interval) + 1)]
first = files[0]
key = "preflop, 0.48, 2, 3, 0, call"

total = 0
data = []
for i in files:
    f = open(i)
    for line in f:
        if key in line:
            total += 1
            data.append(float(line.strip().split(", ")[6][1:]))
            # print(line)

print(total)
print(data)
for line in first:
    # print(line.strip().split(", "))
    # print(line.strip().split(", ")[6][1:])
    pass

plt.plot(data, label='test')


# x = np.linspace(0, 2, 100)

# plt.plot(x, x, label='linear')
# plt.plot(x, x*2, label='quadratic')
# plt.plot(x, x**3, label='cubic')

# plt.xlabel('x label')
# plt.ylabel('y label')

plt.title("Simple Plot")

# plt.legend()

plt.show()

value = [["" for x in range(20)] for x in range(1788)]
# print(value)
# for i in first:
#     line = i.strip().split(" ")
#     n = n + 1
    # print("n = " + str(n))
    # value[n][o] = line[6].strip("[,")
    # print(line[6].strip("[,"))
    # print(line)

    # for f in files:
    #     o = o + 1
    #     print("o = " + str(o))
    #     otherline = i.strip().split(" ")
    #     # print(otherline)
    #     # print(value)
    #     if otherline[0] == line[0] and otherline[1] == line[1] and otherline[2] == line[2] and otherline[3] == line[3] and otherline[4] == line[4] and otherline[5] == line[5]:
    #         value[n][o] = otherline[6]
# print(value)

# for f in files:
#     file = open(f)
#     street = file.readline().strip()
#     for i in file:
#         print(i.strip().split(" "));