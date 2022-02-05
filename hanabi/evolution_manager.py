import json
import random
import socket
import statistics
from threading import Thread
from typing import List, Dict, Tuple

from Agent import Agent
from DiscardRule import DiscardRule
from GeneticAgent import GeneticAgent
from HintRule import HintRule
from PlayRule import PlayRule
from SocketAgent import SocketAgent
from user_constants import CHOOSE_STRONG_PARENT_PROB, SAVE_RESULTS_AFTER_EPOCHS


def get_seeded_starting_agent(name: str):
    return GeneticAgent(name, [
        PlayRule(6, 0.95),
        PlayRule(1, 0.6),
        HintRule(1),
        DiscardRule(6, 0.5)
    ])


class AgentScore:
    def __init__(self, agent: GeneticAgent, score: int):
        self.agent = agent
        self.score = score


class Population:
    def __init__(self, agent_scores: List[AgentScore]):
        self.agent_scores = agent_scores
        self.id_counter: int = 0

    def train(self, n_epochs: int):
        for i in range(n_epochs):
            self.kill_random_agent()
            self.add_offspring()
            if i%SAVE_RESULTS_AFTER_EPOCHS == 0:
                with open(f'training_{i}.json', 'w') as f:
                    json.dump(self.to_json_encoded(), f)

    def compute_median_score(self) -> float:
        return statistics.median([agent.score for agent in self.agent_scores])

    def get_population_split(self) -> Tuple[List[int], List[int]]:
        worse_agents = []
        better_agents = []
        for i in range(len(self.agent_scores)):
            if self.agent_scores[i].score < self.compute_median_score():
                worse_agents.append(i)
            else:
                better_agents.append(i)
        return worse_agents, better_agents

    def kill_random_agent(self):
        worse_agents = self.get_population_split()[0]
        kill_index = random.choice(worse_agents)
        self.agent_scores.pop(kill_index)

    def choose_parent(self) -> AgentScore:
        worse_agents, better_agents = self.get_population_split()
        if random.random() < CHOOSE_STRONG_PARENT_PROB:
            return self.agent_scores[random.choice(better_agents)]
        else:
            return self.agent_scores[random.choice(worse_agents)]

    def add_offspring(self):
        offspring = self.choose_parent().agent.crossover(f'id{self.id_counter}', self.choose_parent())
        self.id_counter += 1
        offspring.mutate()
        players = random.sample(self.agent_scores, 3) + offspring
        self.agent_scores.append(offspring)
        new_scores = Population.evaluate_agents([agent.agent for agent in players])
        for i in range(len(players)):
            players[i].score = new_scores[i].score

    def reevaluate_all(self):
        for i in range(0, len(self.agent_scores), 4):
            results = Population.evaluate_agents([agent.agent for agent in self.agent_scores[i:i+4]])
            for j in range(4):
                self.agent_scores[i+j].score = results[j].score

    def to_json_encoded(self):
        return {
            'id': self.id_counter, 'agents': [agent.agent.to_json_encoded() for agent in self.agent_scores]
        }

    @staticmethod
    def from_json_encoded(encoded_object: dict):
        population = Population([AgentScore(GeneticAgent.from_json_encoded(agent), 0)
                                 for agent in encoded_object['agents']])
        population.id_counter = encoded_object['id']
        population.reevaluate_all()
        return population

    @staticmethod
    def initialize_seeded(num_individuals):
        agents = [get_seeded_starting_agent(f'id{agent_id}') for agent_id in range(num_individuals)]
        for agent in agents:
            agent.mutate()
        result = Population([AgentScore(agent, 0) for agent in agents])
        result.id_counter = num_individuals + 1
        result.reevaluate_all()
        return result

    @staticmethod
    def evaluate_agents(agents: List[GeneticAgent]) -> List[AgentScore]:
        socket_agents = [SocketAgent(socket.socket(socket.AF_INET, socket.SOCK_STREAM), agent) for agent in agents]
        threads = [Thread(target=agent.play_game) for agent in socket_agents]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for agent in socket_agents:
            agent.socket.close()
        return [AgentScore(agent.agent, agent.score) for agent in socket_agents]
