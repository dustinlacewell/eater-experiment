import pdb
import itertools
from time import sleep
import random
import curses 

from pyevolve.GSimpleGA import GSimpleGA
from pyevolve import Selectors

from eaters.tile import *
from eaters.peater import Peater, OBJECTS
from eaters.hookabledict import HookableDict
from eaters.genome import *


class CursesApp(object):

    def __init__(self, screen):
        self._start_screen(screen)
        self.delay = 0.0
        self.do_draw = False
        self.paused = False
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
        ga.setPopulationSize(40)
        ga.setGenerations(250)
        ga.setMutationRate(.1)
        ga.selector.set(Selectors.GTournamentSelector)
        ga.minimax = Consts.minimaxType['maximize']
        
        return ga

    def _start_screen(self, screen):
        self.screen = screen
        self.screen.nodelay(1)
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
        self.screen.clear()
        curses.curs_set(self.orig_curs_mode)
        self.screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        self.screen = None

    def populate_world(self, generation, population):
        height, width = self.screen.getmaxyx()
        for y in range(height - 1):
            for x in range(width):
                tile = None
                if x == 0 or x == width - 1:
                    tile = Wall()
                elif y == 0 or y == height - 2:
                    tile = Wall()
                elif random.randint(0, 5) == 0:
                    tile = Plant()
                if tile:
                    self.world[(y, x)] = tile

        for individual in population:
            y = random.randint(2, height - 4)
            x = random.randint(2, width - 4)
            self.peaters.append(Peater(y, x, genome=individual))
        self.buffer = self.world.copy()


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
        if self.cache_dt == 350:
            self.cache_dt = 0
            self.cache = self.buffer

    def handle_keys(self):
        self.paused = False
        c = self.screen.getch()
        if c == ord(' '):
            self.do_draw = not self.do_draw
            self.screen.clear()
        elif c == 339:
            self.delay = min(2.0, self.delay + .001)
        elif c == 338:
            self.delay = max(0.0, self.delay - .001)
        elif c == ord('p'):
            while self.screen.getch() == -1: pass

    def run(self):
        iterations = 0
        running = True
        cache = False
        if self.do_draw:
            self.screen.clear()
        try:
            while running:
                for p in self.peaters:
                    p.update(self.world)
                if self.handle_cache():
                    cache = True
                self.handle_keys()
                if self.do_draw:
                    self._render_world()
                    self.screen.clearok(0)
                    self.screen.refresh()
                    sleep(self.delay)
                if cache:
                    cache = False
                    raise AssertionError()
                iterations += 1
        except AssertionError, e:
            if not self.do_draw:
                self.screen.move(0, 0)
                gen = self.ga.currentGeneration
                msg = self.ga.internalPop.printStats()
                self.screen.addstr(0, 0, "%s (%s): %s" % (gen, self.delay, msg))
                self.screen.clearok(1)
                self.screen.refresh()
                
                
            
        
            
