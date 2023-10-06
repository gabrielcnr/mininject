import itertools

import pytest

index_counter = itertools.count()


@pytest.fixture(autouse=True)
def clear_containers():
    import container
    container._containers_registry.clear()


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

    def __set_name__(self, owner, name):
        from container import Container

        if self.container is not None:
            raise RuntimeError(f'Injectable is already bound to a Container: {self.container.__name__}')

        if not issubclass(owner, Container):
            raise TypeError(f'Injectables must be owned by Container, not {type(owner)}')

        self.__name = name
        self.__index = next(index_counter)
        self.__container = owner

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.name in vars(instance):
            return vars(instance)[self.name]

        value = self.factory(*self.args, **self.kwargs)

        vars(instance)[self.name] = value
        return value

    def __set__(self, instance, value):
        raise AttributeError('Injectables are read-only')


def test_injectable_must_be_owned_by_container():
    with pytest.raises(TypeError):
        class SomeContainer:  # is not an instance of Container
            foo = Injectable(int, 100)


def test_injectable_is_initialized_on_first_access_only():
    from container import Container

    call_count = 0

    def some_int_factory(n):
        nonlocal call_count
        call_count += 1
        return n

    class MyContainer(Container):
        foo = Injectable(some_int_factory, 123)

    assert isinstance(MyContainer.foo, Injectable)

    container = MyContainer()

    assert call_count == 0

    assert container.foo == 123

    assert call_count == 1

    assert container.foo == 123
    assert container.foo == 123

    assert call_count == 1


def test_injectable_is_read_only_in_container_instances():
    from container import Container

    class MyContainer(Container):
        foo = Injectable(int, 123)

    container = MyContainer()

    with pytest.raises(AttributeError, match='Injectables are read-only'):
        container.foo = 456


def test_injected_values_are_presented_in_vars_of_the_instance():
    from container import Container

    class MyContainer(Container):
        foo = Injectable(int, 123)

    container = MyContainer()

    assert container.foo == 123

    assert vars(container) == {'foo': 123}


def test_unbound_injectable():
    foo = Injectable(int, 123)

    assert foo.name is None
    assert foo.index == -1
    assert foo.container is None


def test_cannot_reuse_injectable_in_more_than_one_container():
    from container import Container

    _foo = Injectable(int, 123)

    class MyContainer(Container):
        foo = _foo

    assert _foo.name == 'foo'
    assert _foo.index != -1
    assert _foo.container is MyContainer

    with pytest.raises(RuntimeError, match='Injectable is already bound to a Container'):
        class MyOtherContainer(Container):
            foo = _foo
