#!/usr/bin/env python3

from sys import argv, stdout
from threading import Thread
from typing import Optional, Any, Union, get_args, List

import GameData
import socket

from Agent import GeneticAgent
from SocketAgent import SocketAgent
from constants import *
import time
import logging
from PlayerGameState import CardHints, PlayerGameState
import sys

from RandomSafeAgent import RandomSafeAgent



