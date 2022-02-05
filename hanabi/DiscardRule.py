import random
from typing import Dict, Callable, List, Optional

import GameData
from AbstractRule import AbstractRule, mutate_probability
from PlayRule import get_last_hinted, get_newest, get_oldest, get_highest, get_lowest, get_random
from PlayerGameState import PlayerGameState
from user_constants import MUTATE_RULE_THRESHOLD_SIGMA, MUTATE_RULE_LOGIC_PROB


class DiscardRule(AbstractRule):
    def __init__(self, select_criterion: int, threshold: float):
        self.select_criterion = DiscardRuleCriterionDeserializer[select_criterion]
        self.threshold = threshold

    def apply(self, player_game_state: PlayerGameState) -> Optional[GameData.ClientPlayerDiscardCardRequest]:
        if player_game_state.hint_tokens == 8:
            return None
        possible_indices = [index for index in self.select_criterion(player_game_state)
                            if player_game_state.get_own_hand_statistics()[index].is_useless >= self.threshold]
        if len(possible_indices) == 0:
            return None
        else:
            return GameData.ClientPlayerDiscardCardRequest(player_game_state.player_name, random.choice(possible_indices))

    def mutate(self):
        self.threshold = mutate_probability(self.threshold, MUTATE_RULE_THRESHOLD_SIGMA)
        if random.random() < MUTATE_RULE_LOGIC_PROB:
            self.select_criterion = random.choice(list(DiscardRuleCriterionSerializer.keys()))

    def to_json_encoded(self):
        return {
            'rule_type': 3,
            'criterion': DiscardRuleCriterionSerializer[self.select_criterion],
            'threshold': self.threshold
        }

    @staticmethod
    def from_json_encoded(encoded_object):
        return DiscardRule(encoded_object['criterion'], encoded_object['threshold'])

    @staticmethod
    def create_random():
        return DiscardRule(random.choice(list(DiscardRuleCriterionDeserializer.keys())), random.random())


DiscardRuleCriterionSerializer: Dict[Callable[[PlayerGameState], List[int]], int] = {
    get_last_hinted: 1,
    get_newest: 2,
    get_oldest: 3,
    get_highest: 4,
    get_lowest: 5,
    get_random: 6,
}
DiscardRuleCriterionDeserializer: Dict[int, Callable[[PlayerGameState], List[int]]] = {
    v: k for k, v in DiscardRuleCriterionSerializer.items()
}
