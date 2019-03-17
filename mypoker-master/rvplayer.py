from pypokerengine.players import BasePokerPlayer

class RVPlayer(BasePokerPlayer):

    def declare_action(self, valid_actions, hole_card, round_state):

        community_cards = round_state['community_card']
        street = round_state['street']  # current round

        call_action_info = self.action_based_on_hand(hole_card, community_cards, valid_actions)

        action = call_action_info["action"]
        return action

    def has_high_card(self, cards):
        return ("T" in cards[0]) or ("J" in cards[0]) or ("Q" in cards[0]) or ("K" in cards[0]) or ("A" in cards[0]) \
               or ("T" in cards[1]) or ("J" in cards[1]) or ("Q" in cards[1]) or ("K" in cards[1]) or ("A" in cards[1])

    def has_mediocre_card(self, cards):
        return ("5" in cards[0]) or ("6" in cards[0]) or ("7" in cards[0]) or ("8" in cards[0]) or ("9" in cards[0]) \
               or ("5" in cards[1]) or ("6" in cards[1]) or ("7" in cards[1]) or ("8" in cards[1]) or ("9" in cards[1])

    def has_pair(self, card, community_cards):
        for community_card in community_cards:
            if (card[0][1] in community_card[1]) or (card[1][1] in community_card[1]):
                return True

    def action_based_on_hand(self, hole_card, community_cards, valid_actions):
        # print(hole_card[0])
        # print(hole_card[1])
        # call is action[1], fold is action[0], raise is action[2]
        last_action = len(valid_actions) - 1
        if self.has_pair(hole_card, community_cards):
            call_action_info = valid_actions[last_action]  # call the last action (either call or raise)
        elif self.has_mediocre_card(hole_card) or self.has_high_card(hole_card):
            call_action_info = valid_actions[1]  # call when have mediocre hand
        else:
            call_action_info = valid_actions[0]  # fold when hand is weak
        return call_action_info

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def setup_ai():
    return RVPlayer()