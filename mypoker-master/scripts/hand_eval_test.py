import sys
sys.path.insert(0, '../')
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate, _fill_community_card, _pick_unused_card
from pypokerengine.engine.hand_evaluator import HandEvaluator
import threading
import time

while True:
    hole = gen_cards(input('hole cards: ').strip().split(" "))
    community = gen_cards(input('community cards: ').strip().split(" "))
    print("{} {} {:b}".format(" ".join(list(map(lambda c: str(c), hole))), " ".join(list(map(lambda c: str(c), community))), HandEvaluator.eval_hand(hole, community)))
