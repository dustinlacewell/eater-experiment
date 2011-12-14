from tile import Tile

__tiles__ = list()

def all():
    return __tiles__[:]

def register(cls):
    can_add = issubclass(cls, Tile) \
        and cls not in __tiles__
    if can_add:
        __tiles__.append(cls)


