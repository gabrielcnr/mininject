import pytest

from mininject import container
from mininject.injectable import Injectable
from mininject.mininject import inject


class MyContainer(container.Container):
    foo = Injectable(int, 100)


container_obj = MyContainer()
container_obj.initialize()

@pytest.fixture(autouse=True)
def clear_containers():
    container._containers_registry.clear()


def test_injected_parameters_must_be_present_in_function_signature():
    with pytest.raises(ValueError):
        @inject(y=MyContainer.foo, match='not present in function .* signature')
        def foo(x: int) -> int:
            ...


def test_simple_injection_single_arg():
    @inject(x=MyContainer.foo)
    def foo(x: int) -> int:
        return x

    assert foo() == 100


def test_simple_injection_multiple_arg_injection_first():
    @inject(x=MyContainer.foo)
    def foo(x: int, y: int) -> int:
        return x * y

    assert foo(y=2) == 200


def test_simple_injection_multiple_arg_injection_last():
    @inject(y=MyContainer.foo)
    def foo(x: int, y: int) -> int:
        return y // x

    assert foo(25) == 4  # 100 // 25 = 4


def test_injected_parameter_cannot_be_a_kwarg_with_default_in_the_func():
    """
    Because it does not make sense to inject a value that is
    already present in the function signature.
    """
    with pytest.raises(ValueError):
        @inject(y=MyContainer.foo)
        def foo(x: int, y: int = 100) -> int:
            return x * y


def test_injection_with_multiple_args_when_injected_parameter_is_a_positional_only_arg():
    @inject(x=MyContainer.foo)
    def foo(x: int, /, y: int, z: int) -> int:
        return x + y + z

    assert foo(y=2, z=3) == 105

    assert foo(20, 2, 3) == 25

    assert foo(20, z=5, y=2) == 27

    with pytest.raises(TypeError):
        foo(x=20, y=2, z=3)


def test_values_passed_to_inject_decorator_must_all_be_instances_of_injectable():
    with pytest.raises(TypeError, match='Injected parameter: y must be an instance of Injectable'):
        @inject(x=MyContainer.foo, y='MyContainer.bar')
        def foo(x: int, y: int) -> int:
            ...
