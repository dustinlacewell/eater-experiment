from eaters.hookabledict import HookableDict



class EEWorld(object):
    def __init__(self, height, width):
        self.height = height
        self.width = width

    def reset(self):
        self.world.clear()
        self.colors.clear()
        self.buffer.clear()
        self.cache.clear()
        self.agents = list()

    def populate_world(self, generation, population):
        self.generation = generation
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
