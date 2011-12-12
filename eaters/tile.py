class TileChecker(type):
    def __eq__(self, obj):
        return isinstance(obj, self)

class Tile(object):
    __metaclass__ = TileChecker
    char = ''
    def __eq__(self, obj):
        return obj == self.char

    def __str__(self):
        return self.char

    def __repr__(self):
        return self.__str__()

class Space(Tile):
    char = '.'

class Wall(Tile):
    char = '#'

class Plant(Tile):
    char = '%'

