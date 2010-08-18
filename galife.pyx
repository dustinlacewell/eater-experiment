import operator
from itertools import product
from random import random, randint, choice

from pytcod import *

cdef int GENERATION_FRAMELIMIT = 1900
cdef int DEATH_FRAMELIMIT = 1840
cdef int HUNGER_FRAMELIMIT = 1500

cdef int EATER = 207
cdef int MEATER = ord("X")
cdef int PLANT = 197
cdef int WALL = ord("#")
cdef int BLANK = ord(" ")

OBJECTS = [EATER, MEATER, PLANT, WALL, BLANK]

UP, DN, LF, RT = (0, -1), (0, 1), (-1, 0), (1, 0)
DIRECTIONS = [UP, DN, LF, RT]

cdef int TURNLEFT = 0
cdef int TURNRIGHT= 1
cdef int MOVE = 2

ACTIONS = [MOVE,  MOVE, TURNLEFT, TURNRIGHT]
BACTIONS = [TURNLEFT, TURNRIGHT]

LO_COLOR = DARKERORANGE
HI_COLOR = GREEN
PLANT_COLOR = CYAN


cdef class Eater(object):

    BLOCKERS = [EATER, MEATER, WALL]

    cdef readonly int NB_STATES# = 4
    cdef object sim, genome, dir
    cdef readonly int x, y
    cdef int state
    cdef readonly int fitness, hunger
    cdef bint mutated, dead

    OUP = ((-1, -1), UP, (1, -1), (0, -2), (0, 2))
    ODN = ((-1, 1), DN, (1, 1), (0, 2), (0, -2))
    OLF = ((-1, 1), LF, (-1, -1), (-2, 0), (2, 0))
    ORT = ((1, -1), RT, (1, 1), (2, 0), (-2, 0))
    SIGHT_TABLE = {UP:OUP, DN:ODN, LF:OLF, RT:ORT}

    def __cinit__(self, sim, x, y, eyespots, dna=None, states=4):
        self.sim = sim
        self.x = x
        self.y = y
        self.dir = choice(DIRECTIONS)
        self.NB_STATES = states
        self.state = randint(0, self.NB_STATES - 1)

        self.fitness = 0
        self.hunger = randint(0, 1000)
        self.mutated = False
        self.dead = False
        self.genome = []
        self.build_genome(eyespots,dna)

    property color:
        def __get__(self):
            cdef int maxfit
            cdef float lerp
            cdef object color
    
            maxfit = max([e.fitness for e in self.sim.eaters])
            lerp = float(self.fitness) / float(maxfit) if maxfit > 0 else 0.0
            color = LO_COLOR.lerp(HI_COLOR, lerp)
            if self.hunger >= HUNGER_FRAMELIMIT:
                return choice([color, WHITE])
            return color
    

    property facing:
        def __get__(self):
            cdef int dx, dy
            combo = []

            for odir in self.SIGHT_TABLE[self.dir]:
                dx, dy = self.x + odir[0], self.y + odir[1]
                combo.append(self.sim.item_at(dx, dy)[0])
            return tuple(combo)

    property dna:
        def __get__(self):
            cdef int idx
            code = []
            
            for idx, statemap in enumerate(self.genome):
                statecode = []
                for mapping in statemap.iteritems():
                    statecode.append(mapping)
                code.append(statecode)
            return code

    cdef build_genome(self, eyespots, dna=None):
        cdef int i, facing, newstate
        self.genome = []

        if dna:
            for statecode in dna:
                statemap = {}
                for sight, action in statecode:
                    statemap[sight] = action
                self.genome.append(statemap)
        else:
            for i in range(self.NB_STATES):
                statemap = {}
                for combo in product(OBJECTS, repeat=eyespots):
                    facing = combo[1]
                    choices = BACTIONS if facing in self.BLOCKERS else ACTIONS
                    action = choice(choices)
                    newstate = i
                    while i == newstate:
                        newstate = randint(0, self.NB_STATES - 1)
                    statemap[combo] = (action, newstate)
                self.genome.append(statemap)
            
    cdef wait(self): return

    cdef move(self):
        cdef newx, newy

        newx = self.x + self.dir[0]
        newy = self.y + self.dir[1]
        if self.facing[1] in self.BLOCKERS:
            return
        elif self.facing[1] == PLANT:
            self.fitness += 1
            self.hunger = 0
            self.sim.ehigh_score = max(self.sim.ehigh_score, self.fitness)
            self.sim.plants.remove((newx, newy))
        self.x, self.y = newx, newy

    cdef turnleft(self):
        table = {
            UP: LF, LF: DN, DN: RT, RT: UP}
        self.dir = table[self.dir]

    cdef turnright(self):
        table = {
            UP: RT, RT: DN, DN: LF, LF: UP}
        self.dir = table[self.dir]


    cdef _update(self):
        cdef action, newstate

        self.hunger += 1
        if self.hunger >= HUNGER_FRAMELIMIT and not self.mutated:
            #dna = self.sim.mutate_dna(self.dna)
            #self.build_genome(dna)
            self.mutated = True
        if self.hunger >= DEATH_FRAMELIMIT:
            if self in self.sim.eaters:
                self.sim.eaters.remove(self)
                self.sim.estarved += 1
            if self in self.sim.meaters:
                self.sim.meaters.remove(self)
                self.sim.mstarved += 1
            self.dead = True
            return
        action, newstate = self.genome[self.state][self.facing]
        #if action == WAIT: self.wait()
        if action == TURNLEFT: self.turnleft()
        elif action == TURNRIGHT: self.turnright()
        elif action == MOVE: self.move()
        self.state = newstate

    def update(self):
        self._update()

    cdef _draw(self):
        cdef int x, y
        self.sim.board.put_char(self.x, self.y, EATER, fg=self.color)
        for dx, dy in self.SIGHT_TABLE[self.dir]:
            x = self.x + dx
            y = self.y + dy
            self.sim.board.set_back(x, y, Color(28, 31, 8))

    def draw(self):
        self._draw()

cdef class MeatEater(Eater):
    
    BLOCKERS = [MEATER,  WALL]

    OUP = ((-1, -1), UP, (1, -1), (-2, -1), (0, -2), (2, -1)) #, (-1, -3), (0, -3), (1, -3))
    ODN = ((-1, 1), DN, (1, 1), (-2, 1), (0, 2), (2, 1)) #, (-1, 3), (0, 3), (1, 3))
    OLF = ((-1, 1), LF, (-1, -1), (-1, 2), (-2, 0), (-1, -2)) #, (-3, 1), (-3, 0), (-3, -1))
    ORT = ((1, -1), RT, (1, 1), (1, 2), (2, 0), (1, -2))#, (3, 1), (3, 0), (3, -1))
    SIGHT_TABLE = {UP:OUP, DN:ODN, LF:OLF, RT:ORT}

    COMBOS = [c for c in product([BLANK,EATER,MEATER,WALL], repeat=6)]



    property color:
        def __get__(self):
            color = MAGENTA
            if self.hunger >= HUNGER_FRAMELIMIT:
                return choice([color, WHITE])
            return color

    property facing:
        def __get__(self):
            combo = []
            for odir in self.SIGHT_TABLE[self.dir]:
                dx, dy = self.x + odir[0], self.y + odir[1]
                item = self.sim.item_at(dx, dy)[0]
                combo.append(BLANK if item == PLANT else item)
            return tuple(combo)


    cdef move(self):
        cdef newx, newy
        newx = self.x + self.dir[0]
        newy = self.y + self.dir[1]
        if self.facing[1] in self.BLOCKERS:
            return
        elif self.facing[1] == EATER:
            self.fitness += 1
            self.hunger = 0
            victim = self.sim.item_at(newx, newy)
            self.sim.eaters.remove(victim[1])
            self.sim.deaths.append((newx, newy))
            self.sim.mhigh_score = max(self.sim.mhigh_score, self.fitness)
        self.x, self.y = newx, newy

    cdef draw(self):
        cdef int x, y

        self.sim.board.put_char(self.x, self.y, MEATER, fg=self.color)
        for dx, dy in self.SIGHT_TABLE[self.dir]:
            x = self.x + dx
            y = self.y + dy
            self.sim.board.set_back(x, y, Color(28, 31, 8))



cdef class Simulation(object):
    cdef object window, board
    cdef object eaters, meaters
    cdef object deaths, plants
    cdef int width, height
    cdef int nb_eaters, nb_meaters
    cdef float plant_chance, crossover_chance, mutation_chance
    cdef int generation_framelimit, hunger_framelimit, death_framelimit
    cdef int estarved, mstarved
    cdef int ehigh_score, mhigh_score
    cdef int generation, frame_counter
    cdef bint done   

    def __cinit__(self, window, int screen_width, int screen_height,
        int nb_eaters, int nb_meaters, 
        float plant_chance, float crossover_chance, float mutation_chance,
        int generation_framelimit, int hunger_framelimit, int death_framelimit):

        self.window = window
        self.width, self.height = screen_width, screen_height

        self.nb_eaters = nb_eaters
        self.nb_meaters = nb_meaters
        self.plant_chance = plant_chance
        self.crossover_chance = crossover_chance
        self.mutation_chance = mutation_chance


        self.board = Console(screen_width, screen_height)
        self.init_board()

        self.eaters = []
        self.meaters = []

        self.deaths = []
        self.plants = []

        self.eaters = [self.make_eater() for i in range(nb_eaters)]
        self.meaters = [self.make_meater() for i in range(nb_meaters)]

        self.generation = 0

        self.estarved = 0
        self.mstarved = 0

        self.ehigh_score = 0
        self.mhigh_score = 0

        self.frame_counter = 0
        self.done = False

    cdef report_stats(self):
        cdef int efit = 0
        cdef int esum = 0
        cdef int eavg = 0
        cdef int eleft = len(self.eaters)
        cdef int mfit = 0
        cdef int msum = 0
        cdef int mavg = 0
        cdef int mleft = len(self.meaters)
        
        cdef bint highest = None
        for e in self.eaters:
            esum += e.fitness
            if efit < e.fitness:
                efit = e.fitness

        eavg = esum / eleft if eleft else 0

        highest = None
        for m in self.meaters:
            msum += m.fitness
            if mfit < m.fitness:
                mfit = m.fitness
        mavg = msum / mleft if mleft else 0

        return """
EATERS
left: {0} - starved: {1}
fitsum: {2} - fitavg: {3}
highest: {4} - highscore: {5}
MEATERS
left: {6} - starved: {7}
fitsum: {8} - fitavg: {9}
highest: {10} - highscore: {11}
""".format(
            eleft, self.estarved, esum, eavg, efit, self.ehigh_score,
            mleft, self.mstarved, msum, mavg, mfit, self.mhigh_score, eaterlist=self.eaters, meaterlist=self.meaters)
        return p

    cdef _item_at(self, int x, int y):
        for eater in self.eaters:
            if eater.x == x and eater.y == y:
                return (EATER, eater)
        for meater in self.meaters:
            if meater.x == x and meater.y == y:
                return (MEATER, meater)
        if (x, y) in self.plants:
            return (PLANT, None)
        if 1 == x or x ==  self.width - 1 or y == 1 or y ==  self.height - 1:
            return (WALL, None)
        return (BLANK, None)

    def item_at(self, x, y):
        return self._item_at(x, y)

    cdef init_board(self):
        self.frame_counter = 0
        self.ehigh_score = 0
        self.mhigh_score = 0
        self.estarved = 0
        self.mstarved = 0

        cdef int i, j

        self.deaths = []
        self.plants = []
        # plant seed
        for i in range(4, self.width - 4):
            for j in range(4, self.height - 4):
                if random() <= self.plant_chance:
                    self.plants.append((i, j))


    cdef _render_board(self):
        self.board.clear()

        cdef int x, y

        for x, y in self.deaths:
            self.board.set_back(x, y, RED)

        for x, y in self.plants:
            self.board.put_char(x, y, PLANT, PLANT_COLOR)

        for eater in self.eaters:
            eater.draw()        
        for meater in self.meaters:
            meater.draw()        

    def render_board(self):
        self._render_board()

    cdef make_eater(self, dna=None):
        cdef int x, y
        while True:
            x = randint(2, self.width - 2)
            y = randint(2, self.height - 2)
            if self.item_at(x, y)[0] == BLANK:
                new_eater = Eater(self, x, y, 5, dna)
                return new_eater

    cdef make_meater(self, dna=None):
        cdef int x, y
        while True:
            x = randint(2, self.width - 2)
            y = randint(2, self.height - 2)
            if self.item_at(x, y)[0] == BLANK:
                new_meater = MeatEater(self, x, y, 6, dna)
                return new_meater

    cdef _update(self):
        self.frame_counter += 1

        for eater in self.eaters:
            eater.update()

        for meater in self.meaters:
            meater.update()
            
        if not self.meaters:
            stats = self.report_stats()
            print "No prey left..."
            self.board.write(35, 35, stats, ALIGNCENTER)
            self.frame_counter = 0
            self.reset_population()
            return 

        if self.frame_counter >= GENERATION_FRAMELIMIT:
            self.frame_counter = 0
            stats = self.report_stats()
            print "Times up! Hold please."
            self.board.write(35, 35, stats, ALIGNCENTER)
            self.new_generation()
   
    def update(self):
        self._update()            

    cdef get_roulette(self, pop):
        cdef float fitsum = 0.0
        cdef float propsum = 0.0
        pop.sort(key=operator.attrgetter('fitness'))
        breeders = [b for b in pop if b.fitness]
        for e in breeders:
            fitsum += e.fitness
        for e in breeders:
            propsum +=  e.fitness / fitsum if fitsum != 0.0 else 0.0
        return fitsum, propsum, breeders

    cdef get_parents(self, float fitsum, float propsum, float breeders):
        cdef int i
        cdef bint winner 
        cdef float roulette, rsum

        parents = []
        for i in range(2):
            winner = None
            roulette = random()
            rsum = 0.0

            for e in breeders:
                prob = e.fitness / fitsum if fitsum != 0.0 else 0.0
                rsum += prob
                if rsum > roulette:
                    parents.append(e)
                    break
        return parents

    cdef get_offspring(self, p1, p2):
        cdef int state

        dna1, dna2 = p1.dna, p2.dna
        newdna = []
        for state in range(p1.NB_STATES):
            if self.crossover_chance > random():
                split_point = choice(range(len(dna1[state])))
                newdna.append( dna1[state][:split_point] + dna2[state][split_point:] )
            else:
                newdna.append(choice([dna1[state], dna2[state]]))
        #newdna = self.mutate_dna(newdna)
        if isinstance(p1, MeatEater):
            return self.make_meater(newdna)
        else:
            return self.make_eater(newdna)

    cdef mutate_dna(self, dna):

#        for idx, statecode in enumerate(dna):
#            for idx2, mapping in enumerate(statecode):
#                if random() <= self.mutation_chance:
        if True:
            for x in range(25):
                statecode = choice(dna)
                idx = dna.index(statecode)
                for x in range(25):
                    mapping  = choice(statecode)
                    idx2 = statecode.index(mapping)
                    sight, behavior = mapping
                    action, newstate = behavior
                    flip = choice([True, False])
                    if flip:
                        newstate = randint(0, len(dna)-1)
                    else:
                        if len(dna) == Eater.NB_STATES:
                            blockers = Eater.BLOCKERS
                        else:
                            blockers = MeatEater.BLOCKERS
                        choices = BACTIONS if sight[1] in blockers else ACTIONS
                        action = choice(choices)
                    dna[idx][idx2] = (sight, (action, newstate))
        return dna

    cdef _new_generation(self):
        cdef int i
        if self.eaters:
            newpop = []
            roulette = self.get_roulette(self.eaters)
            if not roulette[2] or roulette[0] < 2:
                self.eaters = [self.make_eater() for i in range(self.nb_eaters)]
            else:
                for i in range(self.nb_eaters):
                    parents = self.get_parents(roulette[0], roulette[1], roulette[2])
                    newpop.append(self.get_offspring(parents[0], parents[1]))
                    self.eaters = newpop
        else:
            self.eaters = [self.make_eater() for i in range(self.nb_eaters)]

        if self.meaters:
            newpop = []
            roulette = self.get_roulette(self.meaters)
            if not roulette[2]:
                self.meaters = [self.make_meater() for i in range(self.nb_meaters)]
            else:
                for i in range(self.nb_meaters):
                    parents = self.get_parents(roulette[0], roulette[1], roulette[2])
                    newpop.append(self.get_offspring(parents[0], parents[1]))
                    self.meaters = newpop
        else:
            self.meaters = [self.make_meater() for i in range(self.nb_meaters)]

        self.init_board()

    def new_generation(self):
        self._new_generation()

    cdef reset_population(self):
        self.eaters = [self.make_eater() for i in range(self.nb_eaters)]
        self.meaters = [self.make_meater() for i in range(self.nb_meaters)]
        self.generation = 0
        self.init_board()

cdef class SimWindow:        
    cdef object window, sim
    cdef int screen_width, screen_height

    def __cinit__(self, int screen_width, int screen_height,
        int nb_eaters, int nb_meaters, 
        float plant_chance, float crossover_chance, float mutation_chance,
        int generation_framelimit, int hunger_framelimit, int death_framelimit,
        int renderer=RENDER_GLSL):
        
        self.screen_width, self.screen_height = screen_width, screen_height

        self.sim = Simulation(self, screen_width, screen_height,
                   nb_eaters, nb_meaters,
                   plant_chance, crossover_chance, mutation_chance,
                   generation_framelimit, hunger_framelimit, death_framelimit)

    def run(self):
        self._run()

    cdef _run(self):
        self.window = Window(self.screen_width, self.screen_height, "Eater Experiment")
        self.window.fps = 30

        cdef bint done, skipframe
        cdef object ekey

        done = False
        while done == False:
            skipframe = False
            if self.window.is_key_pressed(K_RIGHT):
                self.window.fps = 90
            elif self.window.is_key_pressed(K_LEFT):
                self.window.fps = 15
            elif self.window.is_key_pressed(K_UP):
                self.window.fps = 0
                skipframe = True
            else:
                self.window.fps = 30
    
            ekey = self.window.check_for_key(PRESSED)
            if ekey.vkey == K_DOWN:
                self.sim.new_generation()
                continue
            self.sim.update()
    
            if ekey.vkey != K_NONE:
                if ekey.vkey == K_ESCAPE:
                    print self.sim.report_stats()
                    done = True
    
            if not skipframe:
                self.sim.render_board()
                self.sim.board.write(50, 85, self.sim.report_stats(), ALIGNCENTER)
    
                self.window.clear()
                self.window.blit_c(0, 0, self.sim.board, 0, 0, self.sim.width, self.sim.height, 1.0, 1.0)
                self.window.print_frame(0, 0, self.sim.width, self.sim.height, "Eater Generation {0} (E:{1}/M:{2}) - Timeleft:{3} - {4}FPS ".format(self.sim.generation, self.sim.ehigh_score, self.sim.mhigh_score,GENERATION_FRAMELIMIT - self.sim.frame_counter, self.window.fps), empty=False)
            self.window.flush()
