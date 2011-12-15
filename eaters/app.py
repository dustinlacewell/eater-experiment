import pdb
import itertools
from time import sleep
import random
import curses 

from pyevolve.GSimpleGA import GSimpleGA
from pyevolve import Selectors

from eaters.options import o
from eaters import tiles
from eaters.tiles.basic import *
from eaters.peater import Peater
from eaters.hookabledict import HookableDict
from eaters.genome import *

# Keybindings
o['app.binds.drawmode'] = 9
o['app.binds.quit'] = 32
o['app.binds.delayup'] = 339
o['app.binds.delaydown'] = 338
o['app.binds.pause'] = ord('p')
o['app.binds.tail'] = ord('t')
# Rendering
o['app.render.startup'] = True
o['app.render.mindelay'] = 0.0
o['app.render.maxdelay'] = 0.3
o['app.render.delaydiff'] = 0.01
o['app.render.delay'] = 0.0
o['app.render.trail'] = True
o['app.render.trailsteps'] = 500
o['app.render.trailcolor'] = 3

# GA General
o['ga.general.population'] = 5
o['ga.general.generations'] = 100
o['ga.general.staleticks'] = 350
# GA Evaluation
o['ga.evaluator.elites'] = 2
o['ga.evaluator.minimax'] = 'maximize'
# GA Crossover
o['ga.crossover.rate'] = 0.9
o['ga.crossover.elites'] = 2
o['ga.mutation.rate'] = 0.1

class CursesApp(object):

    def __init__(self, screen):
        self._start_screen(screen)
        self.initialize_options()
        self.initialize_evolver()

    def start(self):
        self.ga.evolve(self.initialize_world)

    def initialize_options(self, **kwargs):
        self.king = None
        self.delay = o.app.render.delay
        self.draw = o.app.render.startup
        self.paused = False

    def initialize_evolver(self):
        # get all tiles
        keys = list(itertools.product(tiles.all(), repeat=4))
        # create sample with all possible genome keys
        sample = GMap(keys, Peater.choices, nstates=8)
        sample.evaluator.set = GMapEvaluator
        # initialize evolver
        ga = GSimulationGA(sample)
        ga.setPopulationSize(o.ga.general.population)
        ga.setGenerations(o.ga.general.generations)
        ga.setCrossoverRate(o.ga.crossover.rate)
        ga.setMutationRate(o.ga.mutation.rate)
        ga.setElitismReplacement(o.ga.crossover.elites)
        ga.setElitism(o.ga.crossover.elites > 0)
        ga.selector.set(Selectors.GTournamentSelector)
        ga.minimax = Consts.minimaxType[o.ga.evaluator.minimax]
        self.ga = ga

    def initialize_world(self, generation, population):
        self.world = HookableDict()
        self.world.hook('setitem', self.world_changed)
        self.buffer = dict()
        self.colors = dict()
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
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        if self.king and o.app.render.trail:
            self.king.eraser = []
            for y, x in (coord for coord, draw in self.king.trail.iteritems() if draw):
                self.colors[(y, x)] = o.app.render.trailcolor
                self.king.trail[(y, x)] = False
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


    def handle_keys(self):
        self.paused = False
        c = self.screen.getch()
        # drawmode
        if c == o.app.binds.drawmode:
            self.draw = not self.draw
            self.screen.clear()
        elif c == o.app.binds.trail:
            o.app.render.trailmode = not o.app.render.trailmode
        # quit
        elif c == o.app.binds.quit:
            return False
        # delay up
        elif c == o.app.binds.delayup:
            self.delay = min(o.app.render.maxdelay, 
                             self.delay + o.app.render.delaydiff)
        # delay down
        elif c == o.app.binds.delaydown:
            self.delay = max(o.app.render.mindelay, 
                             self.delay - o.app.render.delaydiff)
        # pause
        elif c == o.app.binds.pause:
            while self.screen.getch() == -1: pass
        return True

    def handle_agents(self):
        for p in self.peaters:
            p.update(self.world, self.colors)
            if self.king is None or p.genome.simscore > self.king.genome.simscore:
                if self.king:
                    for y, x in self.king.trail:
                        self.screen.chgat(y, x, 1, curses.color_pair(1))
                        self.king.trail[y, x] = True
                self.king = p
                for coord in self.king.trail:
                    self.king.trail[coord] = True
        return True

    def run(self):
        self.king = None
        total_score = 0
        twf = 0 # ticks without fitness
        iterations = 0
        running = True
        if self.draw:
            self.screen.clear()
        while running:
            running = (self.handle_agents()
                   and self.handle_keys())
            new_total = sum(e.genome.simscore for e in self.peaters)
            if new_total == total_score:
                twf += 1
            else:
                twf = 0
                total_score = new_total
            if twf > o.ga.general.staleticks:
                running = False

            if self.draw:
                self._render_world()
                self.screen.clearok(0)
                self.screen.refresh()
                sleep(self.delay)
            iterations += 1
        if not self.draw:
            self.screen.move(0, 0)
            gen = self.ga.currentGeneration
            msg = self.ga.internalPop.printStats()
            self.screen.addstr(0, 0, "%s (%s): %s" % (gen, self.delay, msg))
            self.screen.clearok(1)
            self.screen.refresh()
        
            
