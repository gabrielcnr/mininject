import pytest

from mininject.container import Container, _containers_registry
from mininject.injectable import Injectable


@pytest.fixture(autouse=True)
def clear_containers():
    _containers_registry.clear()


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
