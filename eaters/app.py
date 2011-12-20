import pudb
import itertools
import random
import curses 
import _curses
import urwid

from pyevolve import Selectors

from eaters.genome import *
from eaters.widgets import *
from eaters.peater import Peater
from eaters import tiles
from eaters.tiles.basic import *
from eaters.hookabledict import HookableDict
from eaters.options import o

import time

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
o['app.render.maxdelay'] = 0.2
o['app.render.delaydiff'] = 0.01
o['app.render.delay'] = 0.0
o['app.render.trail'] = True
o['app.render.trailcolor'] = 3
o['app.render.king'] = True
o['app.render.kingcolor'] = 2
# GA General
o['ga.general.population'] = 40
o['ga.general.generations'] = 1000
o['ga.general.staleticks'] = 350
# GA Evaluation
o['ga.evaluator.elites'] = 0
o['ga.evaluator.minimax'] = 'maximize'
# GA Crossover
o['ga.crossover.rate'] = 0.9
o['ga.crossover.elites'] = 2
o['ga.mutation.rate'] = 0.1


class CursesApp(object):

    def __init__(self):
        self.palette = [('I say', 'default,bold', 'default', 'bold'),]
        self.initialize_options()
        self.initialize_screen()
        self.initialize_evolver()
        self.run_iter = self.run()

    def start(self):
        try:
            self.screen.start()
            self.widget = EaterScreenWidget(self)
            self.loop = CursesBufferLoop(self.widget, self.palette,
                                         unhandled_input=self.handle_input,
                                         screen=self.screen)
            self.loop.set_alarm_in(0.0, self.loop_cb, None)
            self.loop.run()
        finally:
            self.screen.stop()

    def handle_input(self, input):
        if input == 'enter':
            command = self.widget.get_command()
            if command == "skip":
                self.running = False
            if command == "top":
                self.widget.log("King fitness: %d" % self.king.genome.simscore)
            if command == "quit":
                raise urwid.ExitMainLoop()


    def initialize_options(self, **kwargs):
        self.king = None
        self.delay = o.app.render.delay
        self.draw = o.app.render.startup
        self.paused = False
        self.stale_ticks = 0

    def initialize_screen(self):
        self.screen = BufferScreen()
        self.buffer = self.screen.chbuf('main')
        self.colors = self.screen.cobuf('main')

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
        self.screen.clear_all_bufs()
        self.screen.dirty = True
        self.screen.clear()
        self.peaters = list()
        self.populate_world(generation, population)
        self.stale_ticks = 0
        self.total_score = 0
        self.king = None
        
    def populate_world(self, generation, population):
        width, height = self.widget.buffer.size
        char = 5
        for y in range(height):
            for x in range(width):
                tile = None
                if x == 0 or x == width - 1:
                    tile = Wall()
                    char += 1
                elif y == 0 or y == height - 1:
                    tile = Wall()
                    char += 1
                elif random.randint(0, 5) == 0:
                    tile = Plant()
                if tile:
                    self.world[(y, x)] = tile

        for individual in population:
            y = random.randint(2, height - 4)
            x = random.randint(2, width - 4)
            self.peaters.append(Peater(y, x, genome=individual))
        self.buffer.clear()
        for key, val in self.world.items():
            self.buffer[key] = val

    def world_changed(self, coord, tile):
        self.buffer[coord] = tile

    def _render_trail(self):
        if self.king and o.app.render.trail:
            for coord, draw in self.king.trail.iteritems():
                self.colors[coord] = o.app.render.trailcolor
                self.king.trail[coord] = False

    def _render_king(self):
        if self.king:
            coord = self.king.y, self.king.x
            self.colors[coord] = o.app.render.kingcolor

    def handle_timeout(self):
        new_total = sum(e.genome.simscore for e in self.peaters)
        if new_total == self.total_score:
            self.stale_ticks += 1
        else:
            self.stale_ticks = 0
        self.total_score = new_total
        if self.stale_ticks > o.ga.general.staleticks:
            return False
        return True

    def handle_agents(self):
        curses.init_pair(1, curses.COLOR_WHITE, -1)
        for p in self.peaters:
            p.update(self.world, self.colors)
        for p in self.peaters:
            if self.king is None or p.genome.simscore > self.king.genome.simscore:
                if self.king:
                    for y, x in self.king.trail:
                        self.colors[(y, x)] = 1
                        self.king.trail[y, x] = True
                self.king = p
                for coord in self.king.trail:
                    self.king.trail[coord] = True
        self._render_trail()
        self._render_king()
        return True

    def loop_cb(self, loop, user_data=None):
        self.run_iter.next()

    def run(self):
        for gen, pop in self.ga.evolve():
            self.initialize_world(gen, pop)
            self.widget.log("Generation: %d" % gen)
            iterations = 0
            self.running = True
            while self.running:
                if iterations % 40 == 0:
                    self.loop.screen.dirty = True

                self.running = (self.handle_agents()
                           and self.handle_timeout())
                iterations += 1
                self.loop.set_alarm_in(0.001, self.loop_cb)
                yield iterations
            self.loop.set_alarm_in(0.001, self.loop_cb)
            yield iterations
        raise urwid.ExitMainLoop()
            
