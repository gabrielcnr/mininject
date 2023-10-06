from functools import cache
from typing import Self

import pytest

from injectable import Injectable

# TODO: ensure only one instance of a Container subclass is created

_initialized_containers = []

_containers_registry = {}


@pytest.fixture(autouse=True)
def clear_containers():
    import container
    container._containers_registry.clear()


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


def test_assert_container_base_class_cannot_be_instantiated():
    with pytest.raises(TypeError, match='Container cannot be instantiated directly'):
        Container()


def test_container_subclasses_cannot_be_modified_after_definition():
    class MyContainer(Container):
        foo = Injectable(int, 100)

    with pytest.raises(TypeError, match='Cannot modify MyContainer'):
        MyContainer.bar = 123

    with pytest.raises(TypeError, match='Cannot delete attributes from MyContainer'):
        del MyContainer.foo

    with pytest.raises(TypeError, match='Cannot modify MyContainer'):
        MyContainer.foo = Injectable(int, 200)


def test_container_can_be_initialized_only_once():
    class MyContainer(Container):
        foo = Injectable(int, 100)

    container = MyContainer()

    container.initialize()

    with pytest.raises(RuntimeError):
        container.initialize()


def test_container_initialization_initializes_all_injectables():
    class MyContainer(Container):
        foo = Injectable(int, 123)
        bar = Injectable(dict, a=1, b='hi')

    container = MyContainer()

    assert vars(container) == {}

    container.initialize()

    assert vars(container) == {'foo': 123, 'bar': {'a': 1, 'b': 'hi'}}

    assert container.foo == 123
    assert container.bar == {'a': 1, 'b': 'hi'}


def test_container_get_injectables():
    class MyContainer(Container):
        some_obj = object()
        foo = Injectable(int, 123)
        some_flag = True
        bar = Injectable(dict, a=1, b='hi')

    injectables = MyContainer.get_injectables()
    assert [name for name, _ in injectables] == ['foo', 'bar']


def test_container_subclass_is_added_to_containers_registry_after_class_definition():
    _containers_registry.clear()

    class MyLittleContainer(Container):
        foo = Injectable(int, 123)

    class MyOtherContainer(Container):
        foo = Injectable(int, 123)

    assert _containers_registry.pop('MyLittleContainer') is MyLittleContainer
    assert _containers_registry.pop('MyOtherContainer') is MyOtherContainer

    assert _containers_registry == {}


def test_containers_cannot_have_same_class_name():
    class MyContainer(Container):
        foo = Injectable(int, 123)

    with pytest.raises(TypeError, match='Cannot create container with duplicate name'):
        class MyContainer(Container):
            foo = Injectable(int, 123)

    assert _containers_registry.pop('MyContainer') is MyContainer
