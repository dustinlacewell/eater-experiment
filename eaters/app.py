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

    def __init__(self, screen, **kwargs):
        self._start_screen(screen)
        self.initialize_options(**kwargs)
        self.initialize_evolver()

    def start(self):
        self.ga.evolve(self.initialize_world)

    def initialize_options(self, **kwargs):
        self.delay = kwargs.get('delay', 0.0)
        self.draw = kwargs.get('draw', False)
        self.paused = False

    def initialize_evolver(self):
        keys = list(itertools.product(OBJECTS, repeat=4))
        sample = GMap(keys, Peater.ACTIONS, 4)
        sample.evaluator.set = GMapEvaluator
        ga = GSimulationGA(sample)
        ga.setPopulationSize(20)
        ga.setGenerations(25000)
        ga.setMutationRate(.1)
        ga.selector.set(Selectors.GTournamentSelector)
        ga.minimax = Consts.minimaxType['maximize']
        self.ga = ga

    def initialize_world(self, generation, population):
        self.world = HookableDict()
        self.world.hook('setitem', self.world_changed)
        self.buffer = dict()
        self.colors = dict()
        self.cache = dict()
        self.cache_dt = 0
        self.peaters = list()
        self.populate_world(generation, population)
        self.run()
        
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
        self.buffer = dict()
        for key, val in self.world.items():
            self.buffer[key] = val

    def _start_screen(self, screen):
        self.screen = screen
        curses.start_color()
        curses.use_default_colors()
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

    def world_changed(self, coord, tile):
        self.buffer[coord] = tile

    def _render_world(self):
        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.init_pair(2, -1, curses.COLOR_GREEN)
        for coord, tile in self.buffer.items():
            y, x = coord
            self.screen.addch(y, x, ord(tile.char), curses.color_pair(1))
        for coord, color in self.colors.items():
            y, x = coord
            self.screen.chgat(y, x, 1, curses.color_pair(color))
        self.buffer = dict()
        self.colors = dict()

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
            self.draw = not self.draw
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
        if self.draw:
            self.screen.clear()
        try:
            while running:
                for p in self.peaters:
                    p.update(self.world, self.colors)
                if self.handle_cache():
                    cache = True
                self.handle_keys()
                if self.draw:
                    self._render_world()
                    self.screen.clearok(0)
                    self.screen.refresh()
                    try:
                        sleep(self.delay)
                    except KeyboardInterrupt:
                        running = False
                if cache:
                    cache = False
                    raise AssertionError()
                iterations += 1
        except AssertionError, e:
            if not self.draw:
                self.screen.move(0, 0)
                gen = self.ga.currentGeneration
                msg = self.ga.internalPop.printStats()
                self.screen.addstr(0, 0, "%s (%s): %s" % (gen, self.delay, msg))
                self.screen.clearok(1)
                self.screen.refresh()
        
            
