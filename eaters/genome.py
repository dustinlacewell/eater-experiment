import pdb
import random
import logging
from time import time
from sys   import platform as sys_platform

from pyevolve.GSimpleGA import GSimpleGA
from pyevolve.GenomeBase import GenomeBase
from pyevolve.GPopulation  import GPopulation
from pyevolve import Util, Consts

def GMapInitializator(genome, **args):
    keys = genome.keys
    nstates = genome.nstates
    
    for state in xrange(nstates):
        for key in keys:
            genome.genome[state][key] = genome.choose()

def GMapMutator(genome, **args):
    if args["pmut"] <= 0.0: return 0
    nkeys = len(genome.keys)
    nstates = genome.nstates
    mutations = args["pmut"] * nkeys * nstates

    if mutations < 1.0:
        mutation = 0
        for state in xrange(nstates):
            for key in genome.keys:
                if Util.randomFlipCoin(args["pmut"]):
                    genome[(state, key)] = genome.choose()
                    mutations += 1
    else:
        for i in xrange(int(round(mutations))):
            state = random.randint(0, nstates - 1)
            key = random.choice(genome.keys)
            genome[(state, key)] = genome.choose()
    return int(mutations)

def GMapCrossoverSinglePoint(genome, **args):
    sister = None
    brother = None
    mom = args['mom']
    dad = args['dad']

    cuts = [random.randint(1, len(mom.keys) - 1) for x in xrange(mom.nstates)]
    mom.keys.sort()
    keys = mom.keys
    cuts = [keys[cut:] for cut in cuts]

    if args['count'] >= 1:
        sister = mom.clone()
        sister.resetStats()
        for state in xrange(mom.nstates):
            keycut = cuts[state]
            for key in keycut:
                sister[(state, key)] = dad[(state, key)]
    if args['count'] == 2:
        brother = dad.clone()
        brother.resetStats()
        for state in xrange(dad.nstates):
            keycut = cuts[state]
            for key in keycut:
                brother[(state, key)] = mom[(state, key)]
    return (sister, brother)
            

def GMapEvaluator(chromosome):
    return chromosome.simscore


class GMapBase:
    """ GMapBase Class - The class for map-based chromosomes

    :param keylist: the list of keys in the genome
    :param vallist: the list of valid values in the genome

    .. versionadded:: 0.6
       Added the *GMapBase* class
    """

    def __init__(self, keys, values, nstates):
        self.keys = keys
        self.values = values
        self.nstates = nstates
        self.simscore = 0

        self.genome = list()
        for x in range(nstates):
            self.genome.append(dict())

    def __eq__(self, other):
        return self.genome == other.genome

    def __len__(self):
        return self.nstates

    def __contains__(self, keypair):
        state, key = keypair
        return key in self.genome[state]

    def __getitem__(self, keypair):
        state, key = keypair
        return self.genome[state].get(tuple(key), self.values[0])

    def __setitem__(self, keypair, value):
        state, key = keypair
        newstate, action = value
        if newstate <= self.nstates and action in self.values:
            self.genome[state][key] = value
        else:
            raise ValueError("%s\n`%s' is not a valid genome value for this species." % (str(self.values), str(value)))

            
    def __iter__(self):
        return iter(self.genome)

    def copy(self, g):
        g.keys = self.keys
        g.values = self.values
        g.nstates = self.nstates
        genome = list()
        for state in self.genome:
            genome.append(state.copy())
        g.genome = genome

    def getInternalGenome(self):
        return self.genome

    def setInternalGenome(self, L):
        self.genome = L



class GMap(GenomeBase, GMapBase):
    evaluator = None
    initializator = None
    mutator = None
    crossover = None

    def __init__(self, keys, values, nstates=1, cloning=False):
        GenomeBase.__init__(self)
        GMapBase.__init__(self, keys, values, nstates)
        if not cloning:
             self.initializator.set(GMapInitializator)
             self.mutator.set(GMapMutator)
             self.crossover.set(GMapCrossoverSinglePoint)
             self.evaluator.set(GMapEvaluator)

    def choose(self):
        return (random.randint(0, self.nstates - 1), random.choice(self.values))
            
    def copy(self, g):
        GenomeBase.copy(self, g)
        GMapBase.copy(self, g)

    def clone(self):
        newobj = GMap(self.keys, self.values, self.nstates)
        self.copy(newobj)
        return newobj


class GSimulationGA(GSimpleGA):
   def evolve(self, simulation_callback, freq_stats=0):
      """ Do all the generations until the termination criteria, accepts
      the freq_stats (default is 0) to dump statistics at n-generation

      Example:
         >>> ga_engine.evolve(freq_stats=10)
         (...)

      :param freq_stats: if greater than 0, the statistics will be
                         printed every freq_stats generation.
      :rtype: returns the best individual of the evolution

      .. versionadded:: 0.6
         the return of the best individual

      """

      self.simulation_callback = simulation_callback
      stopFlagCallback = False
      stopFlagTerminationCriteria = False

      self.time_init = time()

      logging.debug("Starting the DB Adapter and the Migration Adapter if any")
      if self.dbAdapter: self.dbAdapter.open(self)
      if self.migrationAdapter: self.migrationAdapter.start()


      if self.getGPMode():
         gp_function_prefix = self.getParam("gp_function_prefix")
         if gp_function_prefix is not None:
            self.__gp_catch_functions(gp_function_prefix)

      self.initialize()
      self.simulation_callback(self.currentGeneration, self.internalPop)
      self.internalPop.evaluate()
      self.internalPop.sort()
      logging.debug("Starting loop over evolutionary algorithm.")

      try:      
         while True:
            if self.migrationAdapter:
               logging.debug("Migration adapter: exchange")
               self.migrationAdapter.exchange()
               self.internalPop.clearFlags()
               self.internalPop.sort()

            if not self.stepCallback.isEmpty():
               for it in self.stepCallback.applyFunctions(self):
                  stopFlagCallback = it

            if not self.terminationCriteria.isEmpty():
               for it in self.terminationCriteria.applyFunctions(self):
                  stopFlagTerminationCriteria = it

            if freq_stats:
               print self.currentGeneration
               print self.freq_stats
               if (self.currentGeneration % freq_stats == 0) or (self.getCurrentGeneration() == 0):
                  self.printStats()

            if self.dbAdapter:
               if self.currentGeneration % self.dbAdapter.getStatsGenFreq() == 0:
                  self.dumpStatsDB()

            if stopFlagTerminationCriteria:
               logging.debug("Evolution stopped by the Termination Criteria !")
               if freq_stats:
                  print "\n\tEvolution stopped by Termination Criteria function !\n"
               break

            if stopFlagCallback:
               logging.debug("Evolution stopped by Step Callback function !")
               if freq_stats:
                  print "\n\tEvolution stopped by Step Callback function !\n"
               break

            if self.interactiveMode:
               if sys_platform[:3] == "win":
                  if msvcrt.kbhit():
                     if ord(msvcrt.getch()) == Consts.CDefESCKey:
                        print "Loading modules for Interactive Mode...",
                        logging.debug("Windows Interactive Mode key detected ! generation=%d", self.getCurrentGeneration())
                        from pyevolve import Interaction
                        print " done !"
                        interact_banner = "## Pyevolve v.%s - Interactive Mode ##\nPress CTRL-Z to quit interactive mode." % (pyevolve.__version__,)
                        session_locals = { "ga_engine"  : self,
                                           "population" : self.getPopulation(),
                                           "pyevolve"   : pyevolve,
                                           "it"         : Interaction}
                        print
                        code.interact(interact_banner, local=session_locals)

               if (self.getInteractiveGeneration() >= 0) and (self.getInteractiveGeneration() == self.getCurrentGeneration()):
                        print "Loading modules for Interactive Mode...",
                        logging.debug("Manual Interactive Mode key detected ! generation=%d", self.getCurrentGeneration())
                        from pyevolve import Interaction
                        print " done !"
                        interact_banner = "## Pyevolve v.%s - Interactive Mode ##" % (pyevolve.__version__,)
                        session_locals = { "ga_engine"  : self,
                                           "population" : self.getPopulation(),
                                           "pyevolve"   : pyevolve,
                                           "it"         : Interaction}
                        print
                        code.interact(interact_banner, local=session_locals)

            if self.step(): break #exit if the number of generations is equal to the max. number of gens.

      except KeyboardInterrupt:
         logging.debug("CTRL-C detected, finishing evolution.")
         if freq_stats: print "\n\tA break was detected, you have interrupted the evolution !\n"

      if freq_stats != 0:
         self.printStats()
         self.printTimeElapsed()

      if self.dbAdapter:
         logging.debug("Closing the DB Adapter")
         if not (self.currentGeneration % self.dbAdapter.getStatsGenFreq() == 0):
            self.dumpStatsDB()
         self.dbAdapter.commitAndClose()
   
      if self.migrationAdapter:
         logging.debug("Closing the Migration Adapter")
         if freq_stats: print "Stopping the migration adapter... ",
         self.migrationAdapter.stop()
         if freq_stats: print "done !"

      return self.bestIndividual()

   def step(self):
      """ Just do one step in evolution, one generation """
      genomeMom = None
      genomeDad = None

      newPop = GPopulation(self.internalPop)
      logging.debug("Population was cloned.")
      
      size_iterate = len(self.internalPop)

      # Odd population size
      if size_iterate % 2 != 0: size_iterate -= 1
      crossover_empty = self.select(popID=self.currentGeneration).crossover.isEmpty()
      
      for i in xrange(0, size_iterate, 2):
         genomeMom = self.select(popID=self.currentGeneration)
         genomeDad = self.select(popID=self.currentGeneration)
         
         if not crossover_empty and self.pCrossover >= 1.0:
            for it in genomeMom.crossover.applyFunctions(mom=genomeMom, dad=genomeDad, count=2):
               (sister, brother) = it
         else:
            if not crossover_empty and Util.randomFlipCoin(self.pCrossover):
               for it in genomeMom.crossover.applyFunctions(mom=genomeMom, dad=genomeDad, count=2):
                  (sister, brother) = it
            else:
               sister = genomeMom.clone()
               brother = genomeDad.clone()

         sister.mutate(pmut=self.pMutation, ga_engine=self)
         brother.mutate(pmut=self.pMutation, ga_engine=self)

         newPop.internalPop.append(sister)
         newPop.internalPop.append(brother)

      if len(self.internalPop) % 2 != 0:
         genomeMom = self.select(popID=self.currentGeneration)
         genomeDad = self.select(popID=self.currentGeneration)

         if Util.randomFlipCoin(self.pCrossover):
            for it in genomeMom.crossover.applyFunctions(mom=genomeMom, dad=genomeDad, count=1):
               (sister, brother) = it
         else:
            sister = random.choice([genomeMom, genomeDad])
            sister = sister.clone()
            sister.mutate(pmut=self.pMutation, ga_engine=self)

         newPop.internalPop.append(sister)

      logging.debug("Evaluating the new created population.")
      self.simulation_callback(self.currentGeneration, newPop)
      newPop.evaluate()

      #Niching methods- Petrowski's clearing
      self.clear()

      if self.elitism:
         logging.debug("Doing elitism.")
         if self.getMinimax() == Consts.minimaxType["maximize"]:
            for i in xrange(self.nElitismReplacement):
               if self.internalPop.bestRaw(i).score > newPop.bestRaw(i).score:
                  newPop[len(newPop)-1-i] = self.internalPop.bestRaw(i)
         elif self.getMinimax() == Consts.minimaxType["minimize"]:
            for i in xrange(self.nElitismReplacement):
               if self.internalPop.bestRaw(i).score < newPop.bestRaw(i).score:
                  newPop[len(newPop)-1-i] = self.internalPop.bestRaw(i)

      self.internalPop = newPop
      self.internalPop.sort()

      logging.debug("The generation %d was finished.", self.currentGeneration)

      self.currentGeneration += 1

      return (self.currentGeneration == self.nGenerations)
   
    
