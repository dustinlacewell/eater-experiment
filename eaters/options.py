import pdb

class InnerBag(object):
    def __init__(self, valid=False):
        self.valid = bool(valid)
        self.locked = False

    def __eq__(self, other):
        return self.valid == bool(other)

    def __repr__(self):
        return str(self.valid)

    def __str__(self):
        return str(self.valid)

    def __getattr__(self, name):
        try:
            super(InnerBag, self).__getattr__(name)
        except AttributeError:
            if name != 'locked':
                return InnerBag()

    def __setattr__(self, name, value):
        print "Setting", id(self), name, value
        if not hasattr(self, 'locked'):
            super(InnerBag, self).__setattr__(name, value)
        elif name == 'locked':
            super(InnerBag, self).__setattr__('locked', value)
        elif not self.locked or isinstance(value, InnerBag):
            super(InnerBag, self).__setattr__(name, value)
            super(InnerBag, self).__setattr__('locked', True)
        else:
            print hasattr(self, 'locked')
            raise AttributeError((name, value))


class Bag(object):
    def __init__(self, **kw):
        """Initialise, and set attributes from all keyword arguments."""
        self.__allow_access_to_unprotected_subobjects__=1
        self.__members=[]
        for k in kw.keys():
            setattr(self,k,kw[k])
            self.__remember(k)

    def __remember(self, k):
        """Add k to the list of explicitly set values."""
        if not k in self.__members:
            self.__members.append(k)

    def __getitem__(self, key):
        """Equivalent of dict access by key."""
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError, key

    def __setitem__(self, key, value):
        parts = key.split('.')
        tree = self
        for idx, part in enumerate(parts):
            if idx == len(parts) - 1:
                pdb.set_trace()
                setattr(tree, part, value)
                return
            if hasattr(tree, part):
                obj = getattr(tree, part)
                if isinstance(obj, InnerBag):
                    tree = obj
                    continue
            setattr(tree, part, InnerBag('.'.join(parts[:idx+1])))
            tree = getattr(tree, part)
        self.__remember(key)


    def has_key(self, key):
        return hasattr(self, key)


    def keys(self):
        return self.__members


    def iterkeys(self):
        return self.__members


    def __iter__(self):
        return iter(self.__members)


    def __str__(self):
        """Describe only those attributes explicitly set."""
        s = ""
        for x in self.__members:
            v = getattr(self, x)
            if s: s+=", "
            s += "%s: %s" % (x, `v`)
        return s

opts = Bag()
