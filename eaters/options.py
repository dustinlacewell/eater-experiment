import pdb

class InnerBag(object):
    def __init__(self, bag, ns):
        self.namespace = ns
        self.locked = False
    def __repr__(self):
        return self.namespace

    def __str__(self):
        return self.namespace

    def __setattr__(self, name, value):
        if not hasattr(self, 'locked'):
            super(InnerBag, self).__setattr__(name, value)
        elif not self.locked:
            super(InnerBag, self).__setattr__(name, value)
            self.locked = True
        raise AttributeError('InnerBag is locked.')


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
                setattr(tree, part, value)
                return
            if hasattr(tree, part):
                obj = getattr(tree, part)
                if isinstance(obj, InnerBag):
                    tree = obj
                    continue
            setattr(tree, part, InnerBag(self, '.'.join(parts[:idx+1])))
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
