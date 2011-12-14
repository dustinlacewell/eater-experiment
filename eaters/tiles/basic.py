from eaters import tiles
from eaters.tiles.tile import Tile

class Space(Tile):
    char = '.'
tiles.register(Space)

class Wall(tiles.Tile):
    char = '#'
tiles.register(Wall)

class Plant(tiles.Tile):
    char = '%'
tiles.register(Plant)
