from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.utils.card_utils import gen_cards
import random as rand


class LearningPlayer(BasePokerPlayer):
    opp_num_raises = 0
    opp_num_calls = 0
    opp_num_folds = 0
    self_raises = 0

    def __init__(self):
        self.actionHistory = []
        self.gameHistory = []
        self.table = {}
        self.epsilon = 0.1
        streets = ['preflop', 'flop', 'turn', 'river']
        for i in streets:
            self.table[i] = {}

        # read table
        files = ["./hs_data/flop_500000_200.txt", "./hs_data/river_500000_200.txt", "./hs_data/turn_500000_200.txt"]
        for f in files:
            file = open(f)
            for i in file:
                # print(i.strip().split(" "))
                street, score, _, strength = i.strip().split(" ")
                self.table[street][score] = strength

    def getEHS(self, street, hole_card, community_card):
        score = HandEvaluator.eval_hand(gen_cards(hole_card), gen_cards(community_card))
        print(score)
        if str(score) in self.table[street]:
            return self.table[street][str(score)]
        print("Unseen combination")
        print(street, hole_card, community_card, score)
        # print(self.table[street][str(score)])
        return 0

    def get_opponent_play_style(self):
        aggressive_factor = self.opp_num_raises / (self.opp_num_calls + 0.000000001)  # to prevent divide by 0
        player_tightness = self.opp_num_folds / self.num_rounds_played

        if aggressive_factor > 1 and player_tightness < 0.28:
            return 'conservative/aggressive'
        elif aggressive_factor > 1 and player_tightness >= 0.28:
            return 'loose/aggressive'
        elif aggressive_factor <= 1 and player_tightness < 0.28:
            return 'conservative/passive'
        else:
            return 'conservative/loose'

    def declare_action(self, valid_actions, hole_card, round_state):
        r = rand.random()
        street = round_state['street']
        community_card = round_state['community_card']
        ehs = self.getEHS(street, hole_card, community_card)
        action = ''
        isRandom = ''
        if ehs == 0:
            isRandom = ' (random)'
            ehs = rand.random()
            print('ehs', ehs)
        if ehs > 0.8 and len(valid_actions) == 3:
            action = 'raise'
        elif ehs > 0.2:
            action = 'call'
        else:
            action = 'fold'

        self.actionHistory.append({
            'street': round_state['street'],
            'pot': round_state['pot']['main']['amount'],
            'hole_cards': hole_card,
            'community_cards': community_card,
            'ehs': str(ehs) + isRandom,
            'action': action,
            'valid_actions': valid_actions
        })
        return action  # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        # print("Game start", game_info)
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        # print("Round start", round_count, hole_card, seats)
        pass

    def receive_street_start_message(self, street, round_state):
        # print("Street start", street, round_state)
        pass

    def receive_game_update_message(self, action, round_state):
        # print("Game update", action, round_state)
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        # dict_keys([
        # 'street',
        # 'pot',
        # 'community_card',
        # 'dealer_btn',
        # 'next_player',
        # 'small_blind_pos',
        # 'big_blind_pos',
        # 'round_count',
        # 'small_blind_amount',
        # 'seats',
        # 'action_histories'])
        # print(i['round_state'].keys())
        self.gameHistory.append({
            'action_history': self.actionHistory,
            'result': winners[0],
            'pot': round_state['pot']['main']['amount'],
            'self_stack': round_state['seats'][0]['stack'],
            'opp_stack': round_state['seats'][1]['stack']
        })
        self.actionHistory = []
        pass


def setup_ai():
    return LearningPlayer()
