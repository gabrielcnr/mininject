from functools import cache
from typing import Self

from mininject import Injectable

# TODO: ensure only one instance of a Container subclass is created

_initialized_containers = []

_containers_registry = {}


class ContainerMeta(type):
    """
    Metaclass for the Container classes.

    It ensures that after a Container has been defined, it cannot be modified anymore.
    No new attributes or injectables can be added dynamically, nor existing ones can be modified or deleted.
    """

    def __setattr__(cls, name, value):
        raise TypeError(f'Cannot modify {cls.__name__}')

    def __delattr__(cls, name):
        raise TypeError(f'Cannot delete attributes from {cls.__name__}')


class Container(metaclass=ContainerMeta):
    def __new__(cls):
        if cls is Container:
            raise TypeError('Container cannot be instantiated directly - it must be subclassed')
        return super(Container, cls).__new__(cls)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ in _containers_registry:
            raise TypeError(f'Cannot create container with duplicate name: {cls.__name__}')
        _containers_registry[cls.__name__] = cls

    def initialize(self):
        # do not allow it to initialize twice
        if self in _initialized_containers:
            raise RuntimeError('Container already initialized')

        # go through all the injectables and initialize them
        for name, injectable in self.get_injectables():
            getattr(self, name)  # we need to make the first access to the injectable to initialize it
            # TODO: should check args, kwargs of the injectable and see for dependencies that are also injectables

        _initialized_containers.append(self)  # TODO: should be weakref?

    @classmethod
    @cache
    def get_injectables(cls) -> list[tuple[str, Injectable]]:
        injectables = []
        # go through all the attributes of the container class and yield the ones that are injectables
        for name in dir(cls):
            injectable = getattr(cls, name)  # this does not initialize the injectable (because owner is class)
            if isinstance(injectable, Injectable):
                injectables.append((name, injectable))

        return sorted(injectables, key=lambda x: x[1].index)

    @classmethod
    def get_initialized_container_instance(cls) -> Self | None:
        """
        Returns the container instance if it has been initialized, otherwise returns None.
        """
        for container in _initialized_containers:
            if isinstance(container, cls):
                return container


