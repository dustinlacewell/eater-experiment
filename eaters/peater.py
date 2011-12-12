import time
import random
import itertools

from eaters.tile import *

class Peater(Tile):

    WAIT = 0
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4
    ACTIONS = [WAIT, UP, RIGHT, DOWN, LEFT]

    NSTATES = 3

    char = 'x'

    def __init__(self, y, x):
        self.y = y
        self.x = x
        self.state = 0
        self.genome = self.generate_genome()

    def __str__(self):
        return "x"

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

    def get_neighbors(self, world):
        neighbors = list()
        neighbors.append(world.get((self.y - 1, self.x), Space()))
        neighbors.append(world.get((self.y, self.x + 1), Space()))
        neighbors.append(world.get((self.y + 1, self.x), Space()))
        neighbors.append(world.get((self.y, self.x - 1), Space()))
        _neighbors = list()
        for n in neighbors:
            for cls in OBJECTS:
                if cls.char == n.char:
                    _neighbors.append(cls)
                    break
        return tuple(_neighbors)

    def update(self, world):
        neighbors = self.get_neighbors(world)
        action, state = self.genome[self.state][neighbors]
        if action == 1:
            self.do_up(world, neighbors)
        elif action == 2:
            self.do_right(world, neighbors)
        elif action == 3:
            self.do_down(world, neighbors)
        elif action == 4:
            self.do_left(world, neighbors)

    def do_wait(self, world):
        pass

    def do_up(self, world, neighbors):
        if neighbors[0] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.y -= 1
            world[(self.y, self.x)] = self

    def do_right(self, world, neighbors):
        if neighbors[1] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.x += 1
            world[(self.y, self.x)] = self

    def do_down(self, world, neighbors):
        if neighbors[2] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.y += 1
            world[(self.y, self.x)] = self

    def do_left(self, world, neighbors):
        if neighbors[3] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.x -= 1
            world[(self.y, self.x)] = self


OBJECTS = [Space, Wall, Plant, Peater]
