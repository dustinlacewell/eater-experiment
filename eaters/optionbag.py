class BagOptionException(BaseException):
    def __init__(self, attribute):
        message = "Cannot set uninitialized option `%s'." % attribute
        BaseException.__init__(self, message)

class BagOcclusionException(BaseException):
    def __init__(self, old, new):
        message = "`%s' option would occlude `%s'." % (new, old)
        BaseException.__init__(self, message)

class InnerBag(object):
    '''
    A node in the optionbag tree.
    '''

    def __init__(self, valid=False):
        self.valid = bool(valid)
        self.locked = False

    def __eq__(self, other):
        return self.valid == bool(other)

    def __repr__(self):
        return str(self.valid)

    def __str__(self):
        return str(self.valid)

    def __cmp__(self, other):
        if self.valid and other:
            return True
        return False

    def __nonzero__(self):
        if self.valid:
            return True
        return False

    def __getattr__(self, name):
        if not super(InnerBag, self).__getattribute__('valid'):
            return InnerBag()
        try:
            super(InnerBag, self).__getattribute__(name)
        except AttributeError:
            if super(InnerBag, self).__getattribute__('locked'):
                return InnerBag()
            raise AttributeError()

    def __setattr__(self, name, value):
        if name == 'locked':
            super(InnerBag, self).__setattr__('locked', value)
        elif hasattr(self, 'locked') and getattr(self, 'locked'):
            if hasattr(self, name):
                target = getattr(self, name)
                if not isinstance(target, InnerBag):
                    return super(InnerBag, self).__setattr__(name, value)
            raise BagOptionException(name)
        else:
            super(InnerBag, self).__setattr__(name, value)
            super(InnerBag, self).__setattr__('locked', True)


class optionbag(object):
    '''
    An object that is used for maintaining an
    application's settings. It has been designed
    with both the ease of data-oriented
    initialization and natural access from the 
    code in mind.

    When initializing an optionbag it will be used
    largely like a normal dictionary.

    >>> o = optionbag()
    >>> o['foobar'] = True
    >>> o['foobar]
    True

    Similarly to an AttributeDict, keys and their
    values will automatically be mapped to 
    corresponding attributes.

    >>> o = optionbag()
    >>> o['foobar'] = True
    >>> o.foobar
    True
    
    Interestingly, if one uses dot-notation in the
    key an object tree is created instead.

    >>> o = optionbag()
    >>> o['foo.bar'] = True
    >>> o.foo.bar
    True

    The bag may also be initialized by passing
    it an actual dictionary to it's constructor.

    >>> o = optionbag({'foo.bar.baz':-1})
    >>> o.foo.bar.baz
    -1

    The nodes in the object tree are called
    InnerBags and they have some special properties.
    For example, any attribute that contains child 
    bags of its own will evaluate to True.
    
    >>> o = optionbag({'foo.bar.baz':-1})
    >>> o.foo.bar.baz
    -1
    >>> o.foo.bar
    True
    
    Accessing non-existent attributes on an InnerBag 
    will return a new InnerBag that will evaluate to
    False.

    >>> o = optionbag({'foo.bar.baz':-1})
    >>> o.foo.bar.baz
    -1
    >>> o.foo.biz
    False

    However, accessing non-existent attributes on the
    actual root `optionbag' object will raise a normal
    AttributeError.

    >>> o = optionbag({'foo.bar.baz':-1})
    >>> o.zigzag
    *** AttributeError: 'optionbag' object has no attribute 'zigzag'

    Assigning a value to a node that has not been
    explcitly initialized through the optionbag
    will raise a BagOptionError.

    >>> o = optionbag({'foo.bar.baz':-1})
    >>> o.foo.bar.biz = -1
    *** BagOptionException: Cannot set uninitialized option `biz'

    This includes "parent" nodes of existing
    options.

    >>> o = optionbag({'foo.bar.baz':-1})
    >>> o.foo.bar = -1
    *** BagOptionException: Cannot set uninitialized option `biz'

    Attempting to initialize an option that would
    destroy other branches of the tree will raise
    a BagOcclusionException.

    >>> o = optionbag({'foo.bar.baz':-1})
    >>> o['foo.bar'] = -1
    *** BagOcclusionException: `foo.bar' option would occlude `foo.bar.baz'.

    NOTE: optionbag is *not* a dictionary
    '''
    def __init__(self, defaults={}):
        '''
        Initialise, and set options from default dictionary.
        '''
        self.__options=[]
        for option, value in defaults.iteritems():
            self[option] = value

    def __remember(self, option):
        """Add option to the list tracking indexes."""
        if not option in self.__options:
            self.__options.append(option)

    def __getitem__(self, option):
        '''
        Equivalent of dict access by key.
        '''
        parts = option.split('.')
        node = self
        obj = False
        for attr in parts:
            if hasattr(node, attr):
                obj = getattr(node, attr)
                node = obj
        return obj

    def __check_occlusion(self, option):
        '''
        Check that new option would not occlude
        child options.
        '''
        for optkey in self.__options:
            if optkey.startswith(option + '.'):
                raise BagOcclusionException(optkey, option)

    def __setitem__(self, option, value):
        '''
        Eqivalent of dict assignment with relevent
        effects of this data structure.
        '''
        # Check that new option would not occlude
        # child options
        self.__check_occlusion(option)
        # split attribute option
        parts = option.split('.')
        # start on self
        tree = self
        # for each option part
        for idx, part in enumerate(parts):
            # if last part
            if idx == len(parts) - 1:
                # set attribute on node
                if isinstance(tree, InnerBag):
                    tree.locked = False
                setattr(tree, part, value)
                self.__remember(option)
                return
            # if node has attribute
            tree.locked = False
            if hasattr(tree, part):
                # get attribute as next node
                obj = getattr(tree, part)
                # continue if node is bag
                if isinstance(obj, InnerBag):
                    tree = obj
                    continue
                # otherwise...overwrite with bag
                else:
                    setattr(tree, part, InnerBag('.'.join(parts[:idx+1])))
                    tree = obj
                    continue
            else: # node missing current attribute part
                # new bag attribute
                o = InnerBag('.'.join(parts[:idx+1]))
                setattr(tree, part, o)
                tree = o
                continue

    def has_key(self, option):
        return option in self.__options

    def keys(self):
        return self.__options

    def iterkeys(self):
        return self.__options

    def iteritems(self):
        return ((option, self[option]) for option in self.__options)

    def __iter__(self):
        return iter(self.__options)

    def __str__(self):
        """Describe only those attributes explicitly set."""
        s = ""
        for x in self.__options:
            s += "%s\n" % x
        return s
