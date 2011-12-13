import time
import random
import itertools
import pdb 

from eaters.tile import *

class Agent(Tile):
    WAIT = 0
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4
    ACTIONS = [UP, RIGHT, DOWN, LEFT]

    NSTATES = 4

    char = '?'

    def __str__(self):
        return self.char

    def __init__(self, y, x, genome=None):
        self.y = y
        self.x = x
        self.state = 0
        self.genome = genome
        if genome:
            self.genome.simscore = 1

    def get_neighbors(self, world):
        neighbors = list()
        neighbors.append(world.get((self.y - 1, self.x), Space()))
        neighbors.append(world.get((self.y, self.x + 1), Space()))
        neighbors.append(world.get((self.y + 1, self.x), Space()))
        neighbors.append(world.get((self.y, self.x - 1), Space()))
        for idx, n in enumerate(neighbors):
            for cls in OBJECTS:
                if cls.char == n.char:
                    neighbors[idx] = cls
                    break
        return tuple(neighbors)

    def generate_genome(self):
        genome = list()
        for x in range(self.NSTATES):
            state = dict()
            for key in itertools.product(OBJECTS, repeat=4):
                action = random.choice(self.ACTIONS)
                newstate = random.randint(0, self.NSTATES - 1)
                state[key] = (action, newstate)
            genome.append(state)
        return genome

    def update(self, world):
        neighbors = self.get_neighbors(world)
        state, action = self.genome[(self.state, neighbors)]

    def do_wait(self, world):
        pass

    def do_up(self, world, neighbors):
        if neighbors[0] == Space:
            world[(self.y, self.x)] = Space()
            self.y -= 1
            world[(self.y, self.x)] = self

    def do_right(self, world, neighbors):
        if neighbors[1] == Space:
            world[(self.y, self.x)] = Space()
            self.x += 1
            world[(self.y, self.x)] = self

    def do_down(self, world, neighbors):
        if neighbors[2] == Space:
            world[(self.y, self.x)] = Space()
            self.y += 1
            world[(self.y, self.x)] = self

    def do_left(self, world, neighbors):
        if neighbors[3] == Space:
            world[(self.y, self.x)] = Space()
            self.x -= 1
            world[(self.y, self.x)] = self


class Peater(Agent):
    char = 'x'

    def update(self, world):
        _neighbors = self.get_neighbors(world)
        neighbors = list()
        for n in _neighbors:
            if n in [Wall, Peater]:
                neighbors.append(Wall)
            else:
                neighbors.append(n)
        neighbors = tuple(neighbors)
        state, action = self.genome[(self.state, neighbors)]
        if action == 0:
            self.do_up(world, neighbors)
        elif action == 1:
            self.do_right(world, neighbors)
        elif action == 2:
            self.do_down(world, neighbors)
        elif action == 3:
            self.do_left(world, neighbors)

    def do_wait(self, world):
        pass

    def do_up(self, world, neighbors):
        if neighbors[0] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.y -= 1
            world[(self.y, self.x)] = self
        if neighbors[0] == Plant():
            self.genome.simscore += 1
            self.score = 99

    def do_right(self, world, neighbors):
        if neighbors[1] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.x += 1
            world[(self.y, self.x)] = self
        if neighbors[1] == Plant():
            self.genome.simscore += 1
            self.score = 99

    def do_down(self, world, neighbors):
        if neighbors[2] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.y += 1
            world[(self.y, self.x)] = self
        if neighbors[2] == Plant():
            self.genome.simscore += 1
            self.score = 99

    def do_left(self, world, neighbors):
        if neighbors[3] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.x -= 1
            world[(self.y, self.x)] = self
        if neighbors[3] == Plant():
            self.genome.simscore += 1
            self.score = 99


OBJECTS = [Space, Wall, Plant, Peater]
