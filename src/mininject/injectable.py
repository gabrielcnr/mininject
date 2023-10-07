import itertools
from typing import Any

_index_counter = itertools.count()


class Injectable:
    def __init__(self, factory, *args, **kwargs):
        self.factory = factory
        self.args = args
        self.kwargs = kwargs

        # variables set only when the injectable is bound to a Container subclass
        self.__name = None
        self.__index = -1
        self.__container = None

    @property
    def container(self):
        return self.__container

    @property
    def name(self):
        return self.__name

    @property
    def index(self):
        return self.__index

    def __repr__(self):
        if self.container is None:
            return f'<unbound Injectable({self.factory})>'
        else:
            return f'<Injectable({self.factory.__name__}) bound to {self.container.__name__}.{self.name}>'

    def __set_name__(self, owner, name):
        from mininject import Container

        if self.container is not None:
            raise RuntimeError(f'Injectable is already bound to a Container: {self.container.__name__}')

        if not issubclass(owner, Container):
            raise TypeError(f'Injectables must be owned by Container, not {type(owner)}')

        self.__name = name
        self.__index = next(_index_counter)
        self.__container = owner

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.name in vars(instance):
            return vars(instance)[self.name]

        def resolve_injectable(arg):
            if isinstance(arg, Injectable):
                if isinstance(instance, arg.container):
                    container = instance  # this is how we support dependencies from the same container that is not fully initialized yet
                else:
                    container = arg.container.get_initialized_container_instance()  # the other container must be already initialized
                return _get_injected_value_from_container(arg, container)
            else:
                return arg

        args = [resolve_injectable(arg) for arg in self.args]

        kwargs = {k: resolve_injectable(v) for k, v in self.kwargs.items()}

        value = self.factory(*args, **kwargs)

        vars(instance)[self.name] = value
        return value

    def __set__(self, instance, value):
        raise AttributeError('Injectables are read-only')

    def __getattr__(self, attr):
        import pdb; pdb.set_trace()
        return


def _get_injected_value_from_container(injectable: Injectable, container_instance=None) -> Any:
    if container_instance is None:
        container_cls = injectable.container
        container_instance = container_cls.get_initialized_container_instance()
        if container_instance is None:
            raise RuntimeError(f'Container: {container_cls.__name__} is not initialized')

    return getattr(container_instance, injectable.name)


