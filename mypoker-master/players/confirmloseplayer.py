from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.utils.card_utils import _fill_community_card, _pick_unused_card, gen_cards

# uses monte carlo simulation to estimate the probability of winning
class ConfirmLosePlayer(BasePokerPlayer):

    def montecarlo_simulation(self, nb_player, hole_card, community_card):
        # Do a Monte Carlo simulation given the current state of the game by evaluating the hands

        # get all the community cards, include your own hole card, put it in the community_card array
        community_card = _fill_community_card(community_card, used_card=hole_card + community_card)

        # get all the unused cards based on the community card currently (deck - community_card)
        unused_cards = _pick_unused_card((nb_player - 1) * 2, hole_card + community_card)

        # get 100 possibilities of opponent's hole
        opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(nb_player - 1)]

        # calculate the score of opponent's hand based on the possibilities of opponent's hole
        opponents_score = [HandEvaluator.eval_hand(hole, community_card) for hole in opponents_hole]

        # calculate your current hand's score
        my_score = HandEvaluator.eval_hand(hole_card, community_card)

        # if my current hand is better than all the possibilities of opponent's hand
        if my_score >= max(opponents_score):
            return 1
        else:
            return 0

    # Estimate the ratio of winning games given the current state of the game
    def estimate_win_rate(self, nb_simulation, nb_player, hole_card, community_card=None):
        if not community_card:
            community_card = []

        # Make lists of Card objects out of the list of cards
        community_card = gen_cards(community_card)
        hole_card = gen_cards(hole_card)

        # Estimate the win count by doing a Monte Carlo simulation
        win_count = sum([self.montecarlo_simulation(nb_player, hole_card, community_card) for _ in range(nb_simulation)])

        # Return the average wins for all simulations
        return 1.0 * win_count / nb_simulation

    def __init__(self):
        super().__init__()
        self.call_amount = 0
        self.wins = 0
        self.losses = 0

    def declare_action(self, valid_actions, hole_card, round_state):
        # Estimate the win rate using monte carlo simulation, 500 symbolizes number of simulations
        win_rate = self.estimate_win_rate(100, 2, hole_card, round_state['community_card'])

        # print(str(hole_card[0]) + " " + str(hole_card[1]) + " with win rate " + str(win_rate))

        # Check whether it is possible to call
        can_call = len([item for item in valid_actions if item['action'] == 'call']) > 0

        last_action = valid_actions[len(valid_actions) - 1]

        is_raised = (self.call_amount > 0)

        # If the win rate is large enough, then raise
        if win_rate > 0.5:
            if win_rate > 0.75:
                # If it is extremely likely to win, then raise/call if possible
                action = last_action["action"]
            elif win_rate > 0.6:
                # If it is likely to win, then raise/call if possible
                action = last_action["action"]
            else:
                # If there is a chance to win, then call
                action = 'call'
        else:
            if can_call and is_raised:
                action = 'call'
            else:
                action = 'fold'

        return action


    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        self.call_amount = action['amount']  # get the amount to call, amount = 0 means no raise

    def receive_round_result_message(self, winners, hand_info, round_state):
        is_winner = self.uuid in [item['uuid'] for item in winners]
        self.wins += int(is_winner)
        self.losses += int(not is_winner)

def setup_ai():
    return ConfirmLosePlayer()
