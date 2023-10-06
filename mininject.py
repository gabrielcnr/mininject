import functools
import inspect

import pytest

import container
from injectable import Injectable, _get_injected_value_from_container


class MyContainer(container.Container):
    foo = Injectable(int, 100)


container_obj = MyContainer()
container_obj.initialize()


@pytest.fixture(autouse=True)
def clear_containers():
    container._containers_registry.clear()


def inject(**params):
    def decorator(func):

        sig = inspect.signature(func)

        # all the given params must be present inside the function signature
        for p, injectable in params.items():
            if p not in sig.parameters:
                raise ValueError(f'Injected parameter: {p} not present in function {func.__name__}() signature')
            elif not isinstance(injectable, Injectable):
                raise TypeError(f'Injected parameter: {p} must be an instance of Injectable - got: {type(injectable)}')
            elif sig.parameters[p].default is not inspect.Parameter.empty:
                raise ValueError(f'Injected parameter: {p} cannot have a default value')
            # TODO: if the parameter has a type annotation, check that the type is the same as the one in the container

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            missing = find_missing_args_and_kwargs_on_func_call(func, *args, **kwargs)
            for missing_param in missing:
                if missing_param in params:
                    injectable = params[missing_param]

                    value = _get_injected_value_from_container(injectable)

                    # a positional-only argument cannot be passed as kwargs
                    if sig.parameters[missing_param].kind == inspect.Parameter.POSITIONAL_ONLY:
                        args = list(args)
                        args.insert(list(sig.parameters).index(missing_param), value)
                        args = tuple(args)
                    else:
                        kwargs[missing_param] = value
            return func(*args, **kwargs)

        return wrapper

    return decorator


def find_missing_args_and_kwargs_on_func_call(func, *args, **kwargs):
    sig = inspect.signature(func)
    bound = sig.bind_partial(*args, **kwargs)
    missing = [param for param in sig.parameters.values()
               if (param.name not in bound.arguments and param.default == param.empty)]
    return [m.name for m in missing]


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
