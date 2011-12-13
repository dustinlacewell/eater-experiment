from collections import defaultdict

class HookableDict(dict):
    def __init__(self, *args, **kwargs):
        super(HookableDict, self).__init__(*args, **kwargs)
        self.__hooks = defaultdict(set)

    def hook(self, hookname, func):
        self.__hooks[hookname].add(func)

    def unhook(self, hookname, func):
        if func in self.__hooks[hookname]:
            self.__hooks[hookname].remove(func)

    def __setitem__(self, k, v):
        super(HookableDict, self).__setitem__(k, v)
        for hook in self.__hooks['setitem']:
            hook(k, v)
            
        
