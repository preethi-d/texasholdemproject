from pypokerengine.players import BasePokerPlayer
import random as rand


class LearningPlayer(BasePokerPlayer):

    def __init__(self):
        self.actionHistory = []
        self.gameHistory = []
        self.table = []
        self.epsilon = 0.1

    def declare_action(self, valid_actions, hole_card, round_state):
        r = rand.random()
        if r <= 0.5:
            call_action_info = valid_actions[1]
        elif r <= 0.9 and len(valid_actions) == 3:
            call_action_info = valid_actions[2]
        else:
            call_action_info = valid_actions[0]
        action = call_action_info["action"]
        self.actionHistory.append({
            # 'round_state': round_state,
            'street': round_state['street'],
            'pot': round_state['pot']['main']['amount'],
            'hole_cards': hole_card,
            'community_cards': round_state['community_card'],
            'action': action
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
