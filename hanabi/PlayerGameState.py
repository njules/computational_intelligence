from collections import Counter
from enum import Enum
from functools import reduce
from typing import List, Union, Optional, Dict

import GameData
from user_constants import HintType, Color


class Card:
    """ Card from client point of view (without id). Can represent partially known card. """

    def __init__(self, color: Optional[Color] = None, value: Optional[int] = None):
        self.color = color
        self.value = value

    def __eq__(self, other):
        if isinstance(other, Card):
            if self.color is not None and self.value is not None:
                return self.color == other.color and self.value == other.value
        return False

    def __hash__(self):
        return hash((self.color, self.value))

    def could_equal(self, other) -> bool:
        """ Equal given possibly incomplete information """
        if isinstance(other, Card):
            return (self.color is None or other.color is None or self.color == other.color) and \
                   (self.value is None or other.value is None or self.value == other.value)
        return False

    def __str__(self):
        return f"Card({self.color}, {self.value})"

    @staticmethod
    def make_from_server_card(card):
        return Card(Color(card.color), card.value)


class CardStatistic:
    def __init__(self, card: Card, is_playable: float, is_soon_playable: float, is_useless: float, is_necessary: float):
        self.card = card
        self.is_playable = is_playable
        self.is_soon_playable = is_soon_playable
        self.is_useless = is_useless
        self.is_necessary = is_necessary

    def __str__(self):
        return f"Stats({self.card}, playable: {self.is_playable}, soon: {self.is_soon_playable}," \
               f" useless: {self.is_useless}, necessary: {self.is_necessary}"


class GameCards:
    def __init__(self, game_state: GameData.ServerGameStateData):
        self.table_cards: Dict[Color, List[Card]] \
            = {Color(color): [Card.make_from_server_card(card) for card in game_state.tableCards[color]]
               for color in game_state.tableCards}
        self.player_hands: Dict[str, List[Card]] \
            = {player.name: [Card.make_from_server_card(card) for card in player.hand] for player in game_state.players}
        self.discarded_cards: List[Card] = [Card.make_from_server_card(card) for card in game_state.discardPile]
        self.hand_size = game_state.handSize


class CardHints:
    """ Records information from hints about cards on hand. """

    def __init__(self, player_name: str):
        self.player_name = player_name
        self.cards_info: List[Card] = []
        self.last_hinted: List[int] = []

    def __str__(self):
        return f"Hints({self.cards_info})"

    def fill_hand(self, hand_size: int):
        while len(self.cards_info) < hand_size:
            self.cards_info.append(Card())

    def record_hint(self, hint: GameData.ServerHintData):
        if hint.destination == self.player_name:
            for pos in hint.positions:
                if hint.type == HintType.VALUE.value:
                    self.cards_info[pos].value = hint.value
                elif hint.type == HintType.COLOR.value:
                    self.cards_info[pos].color = Color(hint.value)
            self.last_hinted = hint.positions

    def record_play(self, index_played: int):
        self.cards_info.pop(index_played)
        self.cards_info.append(Card())
        self.last_hinted = []


class CardEvaluator:
    """ Class provides methods to evaluate usefulness about given cards. See CardStatistic for computed metrics. """

    def __init__(self, game_cards: GameCards):
        self.__game_cards = game_cards
        self.__unseen_cards = self.__compute_unseen_cards()
        self.__playable_cards = self.__compute_playable_cards()
        self.__soon_playable_cards = self.__compute_soon_playable_cards()
        self.__useless_cards = self.__compute_useless_cards()
        self.__necessary_cards = self.__compute_necessary_cards()
        self.__card_statistics = self.__compute_card_statistics()

    def __compute_unseen_cards(self):
        unseen_cards = [c for c in ALL_CARDS]
        for card_stack in self.__game_cards.table_cards.values():
            for card in card_stack:
                unseen_cards.remove(card)
        for card in self.__game_cards.discarded_cards:
            unseen_cards.remove(card)
        for hand_cards in self.__game_cards.player_hands.values():
            for card in hand_cards:
                unseen_cards.remove(card)
        return unseen_cards

    def __compute_playable_cards(self) -> List[Card]:
        return [Card(Color(color), len(cards) + 1)
                for color, cards in self.__game_cards.table_cards.items() if len(cards) < 5]

    def __compute_soon_playable_cards(self) -> List[Card]:
        return [Card(card.color, card.value + 1) for card in self.__playable_cards if card.value + 1 <= 5]

    def __compute_useless_cards(self) -> List[Card]:
        return [card
                for card in ALL_CARD_TYPES if card.value < len(self.__game_cards.table_cards[card.color])]

    def __compute_necessary_cards(self) -> List[Card]:
        return [card for card in ALL_CARDS if Counter(self.__unseen_cards)[card] == 1]

    def __compute_single_card_statistic(self, card: Card) -> CardStatistic:
        return CardStatistic(card,
                             card in self.__playable_cards,
                             card in self.__soon_playable_cards,
                             card in self.__useless_cards,
                             card in self.__necessary_cards)

    def __compute_card_statistics(self) -> Dict[Card, CardStatistic]:
        return {card: self.__compute_single_card_statistic(card) for card in ALL_CARD_TYPES}

    def get_single_card_statistic(self, card: Card) -> CardStatistic:
        """ Get information about a known card. """
        return self.__card_statistics[card]

    def get_probable_card_statistic(self, unknown_card: Card) -> CardStatistic:
        """ Get information about a partially known card. """
        possible_cards = [card for card in self.__unseen_cards if card.could_equal(unknown_card)]
        card_counts = reduce(
            lambda counter, card: (counter[0] + float(self.get_single_card_statistic(card).is_playable),
                                   counter[1] + float(self.get_single_card_statistic(card).is_soon_playable),
                                   counter[2] + float(self.get_single_card_statistic(card).is_useless),
                                   counter[3] + float(self.get_single_card_statistic(card).is_necessary),),
            possible_cards, (0, 0, 0, 0))
        return CardStatistic(unknown_card,
                             card_counts[0] / len(possible_cards),
                             card_counts[1] / len(possible_cards),
                             card_counts[2] / len(possible_cards),
                             card_counts[3] / len(possible_cards))


class PlayerGameState:
    def __init__(self, player_name):
        self.player_name = player_name
        self.hint_history = CardHints(player_name)
        self.cards: Optional[GameCards] = None
        self.card_evaluator: Optional[CardEvaluator] = None
        self.hint_tokens = 0
        self.storm_tokens = 0

    def register_hint(self, hint: GameData.ServerHintData):
        self.hint_history.record_hint(hint)

    def register_card_played(self, card_index: int):
        self.hint_history.record_play(card_index)

    def update_game_state(self, game_state: GameData.ServerGameStateData):
        self.cards = GameCards(game_state)
        self.hint_tokens = NUM_HINT_TOKENS - game_state.usedNoteTokens
        self.storm_tokens = game_state.usedStormTokens
        self.hint_history.fill_hand(self.cards.hand_size)
        self.card_evaluator = CardEvaluator(self.cards)

    def get_player_hand_statistics(self) -> Dict[str, List[CardStatistic]]:
        return {player_name: [self.card_evaluator.get_single_card_statistic(Card.make_from_server_card(card))
                              for card in player_cards]
                for player_name, player_cards in self.cards.player_hands.items()}

    def get_own_hand_statistics(self) -> List[CardStatistic]:
        return [self.card_evaluator.get_probable_card_statistic(card) for card in self.hint_history.cards_info]


ALL_CARDS = [Card(color, value) for color in Color for value in [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]]
ALL_CARD_TYPES = [Card(color, value) for color in Color for value in range(1, 6)]

NUM_HINT_TOKENS = 8
