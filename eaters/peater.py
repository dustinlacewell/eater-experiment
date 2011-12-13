import time
import random
import itertools
import pdb 

from eaters.tile import *

# ACTIONS
WAIT = 0
NORTH = 1
EAST = 2
SOUTH = 3
WEST = 4

class Agent(Tile):
    ACTIONS = [NORTH, EAST, SOUTH, WEST]
    CHAR = '?'

    def __init__(self, y, x, genome=None):
        self.y = y
        self.x = x
        self.state = 0
        self.heading = None
        self.genome = genome
        self.actions = (self.do_north,
                        self.do_east,
                        self.do_south,
                        self.do_west,)

    def __str__(self):
        return self.CHAR

    def __nstates__(self):
        return len(self.genome)
    nstates = property(__nstates__)

    def neighbor_north(self, world):
        return world.get((self.y - 1, self.x), Space())
    def neighbor_south(self, world):
        return world.get((self.y + 1, self.x), Space())
    def neighbor_west(self, world):
        return world.get((self.y, self.x - 1), Space())
    def neighbor_east(self, world):
        return world.get((self.y, self.x + 1), Space())

    def neighbor_forward(self, world):
        if self.heading:
            off_y = self.y + self.heading[0]
            off_x = self.x + self.heading[1]
            return world.get((off_y, off_x), Space())
    def neighbor_backward(self, world):
        if self.heading:
            off_y = self.y + -self.heading[0]
            off_x = self.x + -self.heading[1]
            return world.get((off_y, off_x), Space())
    def neighbor_left(self, world):
        if self.heading:
            off_y = self.y + self.heading[1]
            off_x = self.x + self.heading[0]
            return world.get((off_y, off_x), Space())
    def neighbor_right(self, world):
        if self.heading:
            off_y = self.y + -self.heading[1]
            off_x = self.x + -self.heading[0]
            return world.get((off_y, off_x), Space())


    def get_neighbors(self, world):
        neighbors = list()
        if self.heading:
            neighbors.append(self.neighbor_forward(world))
            neighbors.append(self.neighbor_right(world))
            neighbors.append(self.neighbor_backward(world))
            neighbors.append(self.neighbor_left(world))
        else:
            neighbors.append(self.neighbor_north(world))
            neighbors.append(self.neighbor_east(world))
            neighbors.append(self.neighbor_south(world))
            neighbors.append(self.neighbor_west(world))

        for idx, n in enumerate(neighbors):
            for cls in OBJECTS:
                if cls.char == n.char:
                    neighbors[idx] = cls
                    break
        return tuple(neighbors)

    def generate_genome(self):
        genome = list()
        for x in range(self.nstates):
            state = dict()
            for key in itertools.product(OBJECTS, repeat=4):
                action = random.choice(self.ACTIONS)
                newstate = random.randint(0, self.nstates - 1)
                state[key] = (action, newstate)
            genome.append(state)
        return genome

    def update(self, world, colors):
        neighbors = self.get_neighbors(world)
        self.state, action = self.genome[(self.state, neighbors)]
        self.actions[action - 1](neighbors, world, colors)

    def do_wait(self, world):
        pass

    def do_north(self, neighbors, world, colors):
        if neighbors[0] == Space:
            world[(self.y, self.x)] = Space()
            self.y -= 1
            world[(self.y, self.x)] = self

    def do_east(self, neighbors, world, colors):
        if neighbors[1] == Space:
            world[(self.y, self.x)] = Space()
            self.x += 1
            world[(self.y, self.x)] = self

    def do_south(self, neighbors, world, colors):
        if neighbors[2] == Space:
            world[(self.y, self.x)] = Space()
            self.y += 1
            world[(self.y, self.x)] = self

    def do_west(self, neighbors, world, colors):
        if neighbors[3] == Space:
            world[(self.y, self.x)] = Space()
            self.x -= 1
            world[(self.y, self.x)] = self

class Peater(Agent):
    char = 'x'

    def do_north(self, neighbors, world, colors):
        if neighbors[0] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.y -= 1
            world[(self.y, self.x)] = self
        if neighbors[0] == Plant():
            self.genome.simscore += 1
            colors[(self.y, self.x)] = 2

    def do_east(self, neighbors, world, colors):
        if neighbors[1] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.x += 1
            world[(self.y, self.x)] = self
        if neighbors[1] == Plant():
            self.genome.simscore += 1
            colors[(self.y, self.x)] = 2

    def do_south(self, neighbors, world, colors):
        if neighbors[2] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.y += 1
            world[(self.y, self.x)] = self
        if neighbors[2] == Plant():
            self.genome.simscore += 1
            colors[(self.y, self.x)] = 2

    def do_west(self, neighbors, world, colors):
        if neighbors[3] not in [Wall, Peater]:
            world[(self.y, self.x)] = Space()
            self.x -= 1
            world[(self.y, self.x)] = self
        if neighbors[3] == Plant():
            self.genome.simscore += 1
            colors[(self.y, self.x)] = 2


OBJECTS = [Space, Wall, Plant, Peater]
