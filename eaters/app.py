import pdb
import itertools
import time
import random
import curses 

from pyevolve.GSimpleGA import GSimpleGA

from eaters.tile import *
from eaters.peater import Peater, OBJECTS
from eaters.hookabledict import HookableDict
from eaters.genome import *


class CursesApp(object):

    def __init__(self, screen):
        self.screen = screen
        self.ga = self.initialize_evolver()

    def start(self):
        self.ga.evolve(self.initialize_world)

    def initialize_world(self, generation, population):
        self.world = HookableDict()
        self.world.hook('setitem', self.world_changed)
        self.buffer = dict()
        self.cache = dict()
        self.cache_dt = 0
        self.peaters = list()
        self.populate_world(generation, population)
        self.run()
        
    def initialize_evolver(self):
        keys = list(itertools.product(OBJECTS, repeat=4))
        sample = GMap(keys, Peater.ACTIONS, Peater.NSTATES)
        sample.evaluator.set = GMapEvaluator
        ga = GSimulationGA(sample)
        ga.minimax = Consts.minimaxType['maximize']
        return ga

    def _start_screen(self):
        # don't echo keypresses
        curses.noecho()
        # handle keypresses immediately
        curses.cbreak()
        # enable color rendering
        curses.start_color()
        # hide the cursor
        self.orig_curs_mode = curses.curs_set(0)
        # handle special characters
        self.screen.keypad(1)

    def _stop_screen(self):
        curses.curs_set(self.orig_curs_mode)
        self.screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def populate_world(self, generation, population):
        height, width = self.screen.getmaxyx()
        for y in range(height - 1):
            for x in range(width):
                tile = None
                if x == 0 or x == width - 1:
                    tile = Wall()
                elif y == 0 or y == height - 2:
                    tile = Wall()
                elif random.randint(0, 20) == 0:
                    tile = Plant()
                if tile:
                    self.world[(y, x)] = tile

        for individual in population:
            y = random.randint(10, height - 10)
            x = random.randint(10, width - 10)
            self.peaters.append(Peater(y, x, genome=individual))


    def world_changed(self, coord, tile):
        self.buffer[coord] = tile

    def _render_world(self):
        for coord, tile in self.buffer.items():
            x, y = coord
            self.screen.addch(x, y, ord(tile.char))
        self.buffer = dict()

    def _render_world_old(self):
        height, width = self.screen.getmaxyx()
        for y in range(height - 1):
            for x in range(width):
                tile = self.world.get((y, x), Space())
                self.screen.move(y, x)
                self.screen.addch(ord(tile.char))

    def handle_cache(self):
        if self.buffer == self.cache:
            return True
        else:
            self.cache_dt += 1
        if self.cache_dt == 1000:
            self.cache_dt = 0
            self.cache = self.buffer

    def handle_keys(self):
        pass

    def run(self):
        self._start_screen()
        iterations = 0
        running = True
        try:
            while running:
                for p in self.peaters:
                    p.update(self.world)
                if self.handle_cache():
                    raise KeyboardInterrupt()
                self.handle_keys()
                self._render_world()
                self.screen.clearok(0)
                self.screen.refresh()
                iterations += 1
#                time.sleep(.02)
        except KeyboardInterrupt, e:
            self._stop_screen()
            print self.buffer
            print self.cache
            print self.ga.printStats()
            
