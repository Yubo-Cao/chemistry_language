def lazy_loading(func):
    attr = "_lazy@" + func.__name__

    @property
    def _impl(self):
        if not hasattr(self, attr):
            setattr(self, attr, func(self))
        return getattr(self, attr)

    return _impl


def shared_lazy_loading(func):
    attr = "_lazy@" + func.__name__

    @property
    def _impl(self):
        if not hasattr(self.__class__, attr):
            setattr(self.__class__, attr, func(self))
        return getattr(self.__class__, attr)

    return _impl
