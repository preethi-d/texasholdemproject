f = open("handstr.txt")
cards = ["A"] + [str(i) for i in range(2, 10)] + ["T", "J", "Q", "K"]
print(cards)
winrates = {}
for i in cards:
	winrates[i] = {}

for i in f:
	c1, c2, n = i.strip().split(" ")
	winrates[c1][c2] = n
	winrates[c2][c1] = n
	#print("cards: {}{} n: {}".format(c1, c2, n))
	
print(winrates["Q"]["4"])