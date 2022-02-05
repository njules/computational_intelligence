import random
from typing import Dict, Callable, List, Optional, Tuple

import GameData
from AbstractRule import AbstractRule, mutate_probability
from PlayerGameState import PlayerGameState, Card, CardStatistic
from user_constants import MUTATE_RULE_THRESHOLD_SIGMA, MUTATE_RULE_LOGIC_PROB


def choose_card(player_hand_statistics: Dict[str, List[CardStatistic]],
                card_filter: Callable[[CardStatistic], bool]) -> Optional[Tuple[str, Card]]:
    candidates = []
    for player_name, player_cards in player_hand_statistics.items():
        for card in player_cards:
            if card_filter(card):
                candidates.append((player_name, card.card))
    if len(candidates) >= 1:
        return random.choice(candidates)
    else:
        return None


HintRuleCriterionDeserializer: Dict[int, Callable[[CardStatistic], bool]] = {
    1: (lambda card_stat: card_stat.is_playable),
    2: (lambda card_stat: card_stat.is_soon_playable),
    3: (lambda card_stat: card_stat.is_useless),
    4: (lambda card_stat: card_stat.is_necessary),
    5: (lambda card_stat: True),  # random
}
HintRuleCriterionSerializer: Dict[Callable[[CardStatistic], bool], int] = {
    v: k for k, v in HintRuleCriterionDeserializer.items()
}


class HintRule(AbstractRule):
    def __init__(self, select_criterion: int):
        self.select_criterion = HintRuleCriterionDeserializer[select_criterion]

    def apply(self, player_game_state: PlayerGameState) -> Optional[GameData.ClientHintData]:
        if player_game_state.hint_tokens == 0:
            return None
        hint_player_card = choose_card(player_game_state.get_player_hand_statistics(), self.select_criterion)
        if hint_player_card is not None:
            hint_type = random.choice(['color', 'value'])
            hint_value = hint_player_card[1].color.value if hint_type == 'color' else hint_player_card[1].value
            return GameData.ClientHintData(
                player_game_state.player_name,
                hint_player_card[0],
                hint_type,
                hint_value
            )
        else:
            return None

    def mutate(self):
        if random.random() < MUTATE_RULE_LOGIC_PROB:
            self.select_criterion = random.choice(list(HintRuleCriterionSerializer.keys()))

    def to_json_encoded(self):
        return {
            'rule_type': 2,
            'criterion': HintRuleCriterionSerializer[self.select_criterion],
        }

    @staticmethod
    def from_json_encoded(encoded_object):
        return HintRule(encoded_object['criterion'])

    @staticmethod
    def create_random():
        return HintRule(random.choice(list(HintRuleCriterionDeserializer.keys())))
