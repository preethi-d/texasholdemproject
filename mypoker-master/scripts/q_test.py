import sys
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate, _pick_unused_card
from pypokerengine.engine.hand_evaluator import HandEvaluator
from players.learningplayer import LearningPlayer
from players.rvplayer import RVPlayer
epsilon = 0.1
learn_factor = 0.05
discount_factor = 0.5
bb = 0
unseen_hands = 0
unseen_states = 0
num_rounds_this_game = 0

cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']

hole_card = gen_cards(['H' + cards[0], 'D' + cards[0]])
community_card = gen_cards(['H' + cards[3], 'D' + cards[5],'H' + cards[10], 'D' + cards[2], 'H' + cards[2]])
agent_score = HandEvaluator.eval_hand(hole_card, community_card)
num_sim = 100
streets = ['preflop', 'flop', 'turn', 'river']
table = {}
for i in streets:
	table[i] = {}

# read table
files = ["./hs_data/flop_2500000_500.txt", "./hs_data/river_2500000_500.txt", "./hs_data/turn_2500000_500.txt",
		 "./hs_data/preflop_10000.txt"]
for f in files:
	file = open(f)
	street = file.readline().strip()
	for i in file:
		# print(i.strip().split(" "))
		score, strength = i.strip().split(" ")
		table[street][score] = strength
for i in range(num_sim):
	opp_hole_card = _pick_unused_card(2, hole_card+community_card)
	opp_score = HandEvaluator.eval_hand(opp_hole_card, community_card)
	attrs = {'street': 'river', 'ehs': table['river'][agent_score], 'action': 'raise'}
	if agent_score > opp_score:
		reward = 1
	elif agent_score == opp_score:
		reward = 0
	else:
		reward = -1

	update_table(attrs, reward)

def update_table(attrs, reward):
	lf = learn_factor
	q0, c0 = get_table(attrs)
	if not q0:
		q0, c0 = 0, 0
		lf = 1

	q1 = q0 * (1 - lf) + reward * lf
	c1 = c0 + 1
	self.log(
		"q: {} -> {} (r: {}|{}) n: {} state: {}".format(str(q0), str(q1), str(reward), str(lf), str(c1), attrs),
		1)
	self.set_table(attrs, [q1, c1])