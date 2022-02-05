from enum import Enum
from typing import Union

import GameData


class Color(Enum):
    RED = 'red'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    WHITE = 'white'


class HintType(Enum):
    COLOR = 'color'
    VALUE = 'value'


ClientAction = Union[
    GameData.ClientPlayerPlayCardRequest,
    GameData.ClientHintData,
    GameData.ClientPlayerDiscardCardRequest,
]
ActionPerformed = Union[
    GameData.ServerPlayerMoveOk,
    GameData.ServerPlayerThunderStrike,
    GameData.ServerActionValid,
    GameData.ServerHintData,
]

MUTATE_RULE_THRESHOLD_SIGMA = 0.1
MUTATE_RULE_LOGIC_PROB = 0.05
DROP_UNUSED_RULE_PROB = 0.2
DROP_RULE_PROB = 0.01
CREATE_NEW_RULE_PROB = 0.1
MOVE_RULE_UP_PROB = 0.1
MOVE_RULE_TWO_UP_PROB = 0.1
CROSSOVER_SWITCH_RULE_PROB = 0.1
CHOOSE_STRONG_PARENT_PROB = 0.8
SAVE_RESULTS_AFTER_EPOCHS = 10
