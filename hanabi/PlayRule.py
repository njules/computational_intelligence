import random
from typing import Dict, Callable, List, Optional

import GameData
from AbstractRule import AbstractRule, mutate_probability
from PlayerGameState import PlayerGameState
from user_constants import MUTATE_RULE_THRESHOLD_SIGMA, MUTATE_RULE_LOGIC_PROB


def get_last_hinted(player_game_state: PlayerGameState) -> List[int]:
    return player_game_state.hint_history.last_hinted


def get_newest(player_game_state: PlayerGameState) -> List[int]:
    return [player_game_state.cards.hand_size - 1]


def get_oldest(player_game_state: PlayerGameState) -> List[int]:
    return [0]


def get_highest(player_game_state: PlayerGameState) -> List[int]:
    play_index = None
    for idx in range(len(player_game_state.get_own_hand_statistics())):
        if player_game_state.get_own_hand_statistics()[idx].card.value is not None and \
                (play_index is None or player_game_state.get_own_hand_statistics()[idx].card.value > play_index):
            play_index = idx
    return [play_index]


def get_lowest(player_game_state: PlayerGameState) -> List[int]:
    play_index = None
    for idx in range(len(player_game_state.get_own_hand_statistics())):
        if player_game_state.get_own_hand_statistics()[idx].card.value is not None and\
                (play_index is None or player_game_state.get_own_hand_statistics()[idx].card.value < play_index):
            play_index = idx
    return [play_index]


def get_random(player_game_state: PlayerGameState) -> List[int]:
    return [i for i in range(player_game_state.cards.hand_size)]


class PlayRule(AbstractRule):
    def __init__(self, select_criterion: int, threshold: float):
        self.select_criterion = PlayRuleCriterionDeserializer[select_criterion]
        self.threshold = threshold

    def apply(self, player_game_state: PlayerGameState) -> Optional[GameData.ClientPlayerPlayCardRequest]:
        possible_indices = [index for index in self.select_criterion(player_game_state)
                            if player_game_state.get_own_hand_statistics()[index].is_playable >= self.threshold]
        if len(possible_indices) == 0:
            return None
        else:
            max_playability = 0
            play_index = 0
            for i in possible_indices:
                playability = player_game_state.get_own_hand_statistics()[i].is_playable
                if playability > max_playability:
                    max_playability = playability
                    play_index = i
            return GameData.ClientPlayerPlayCardRequest(player_game_state.player_name, play_index)

    def mutate(self):
        self.threshold = mutate_probability(self.threshold, MUTATE_RULE_THRESHOLD_SIGMA)
        if random.random() < MUTATE_RULE_LOGIC_PROB:
            self.select_criterion = random.choice(list(PlayRuleCriterionSerializer.keys()))

    def to_json_encoded(self):
        return {
            'rule_type': 1,
            'criterion': PlayRuleCriterionSerializer[self.select_criterion],
            'threshold': self.threshold
        }

    @staticmethod
    def from_json_encoded(encoded_object):
        return PlayRule(encoded_object['criterion'], encoded_object['threshold'])

    @staticmethod
    def create_random():
        return PlayRule(random.choice(list(PlayRuleCriterionDeserializer.keys())), random.random())


PlayRuleCriterionSerializer: Dict[Callable[[PlayerGameState], List[int]], int] = {
    get_last_hinted: 1,
    get_newest: 2,
    get_oldest: 3,
    get_highest: 4,
    get_lowest: 5,
    get_random: 6,
}
PlayRuleCriterionDeserializer: Dict[int, Callable[[PlayerGameState], List[int]]] = {
    v: k for k, v in PlayRuleCriterionSerializer.items()
}
