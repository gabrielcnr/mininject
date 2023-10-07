import operator

import pytest

from mininject import Injectable, Container


@pytest.fixture(autouse=True)
def clear_containers():
    from mininject import container
    container._containers_registry.clear()


def test_injectable_must_be_owned_by_container():
    with pytest.raises(TypeError):
        class SomeContainer:  # is not an instance of Container
            foo = Injectable(int, 100)


def test_injectable_is_initialized_on_first_access_only():
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
    class MyContainer(Container):
        foo = Injectable(int, 123)

    container = MyContainer()

    with pytest.raises(AttributeError, match='Injectables are read-only'):
        container.foo = 456


def test_injected_values_are_presented_in_vars_of_the_instance():
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
    _foo = Injectable(int, 123)

    class MyContainer(Container):
        foo = _foo

    assert _foo.name == 'foo'
    assert _foo.index != -1
    assert _foo.container is MyContainer

    with pytest.raises(RuntimeError, match='Injectable is already bound to a Container'):
        class MyOtherContainer(Container):
            foo = _foo


def test_injectable_can_depend_on_other_injectables_that_are_already_initialized():
    class MyContainer(Container):
        x = Injectable(int, 100)
        y = Injectable(operator.mul, x, 5)

    container = MyContainer()
    container.initialize()

    assert container.x == 100
    assert container.y == 500


def test_injectable_can_depend_on_other_injectables_from_other_containers_that_are_already_initialized():
    class ContainerA(Container):
        x = Injectable(int, 100)

    class ContainerB(Container):
        y = Injectable(operator.mul, ContainerA.x, 5)

    container_a = ContainerA()
    container_a.initialize()

    container_b = ContainerB()
    container_b.initialize()

    assert container_a.x == 100
    assert container_b.y == 500
