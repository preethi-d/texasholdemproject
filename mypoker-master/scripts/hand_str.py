import sys
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
print(sys.argv[1], "times")
for i in range(len(cards)):
	for j in range(i, len(cards)):
		hole_card = gen_cards(['H' + cards[i], 'D' + cards[j]])
		community_card = gen_cards([])
		print(cards[i], cards[j], estimate_hole_card_win_rate(nb_simulation=int(sys.argv[1]), nb_player=2, hole_card=hole_card, community_card=community_card))