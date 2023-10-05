import functools
import inspect

import pytest


# TODO: decide how to register / declare the containers and how to initialize them
containers = {
    'MyContainer': {
        'foo': 100,
    },
}

def register_container(cls):
    containers[cls.__name__] = cls()
    return cls


@register_container
class MyContainer:
    foo: int = (int, 100)

def inject(**params):

    def decorator(func):

        sig = inspect.signature(func)

        sig_params = list(sig.parameters)

        # all the given params must be present inside the function signature
        for p, p_map in params.items():
            if p not in sig_params:
                raise ValueError(f'Injected parameter: {p} not present in function {func.__name__}() signature')
            elif len([part for part in p_map.split('.') if part]) != 2:
                raise ValueError(f'Injected parameter: {p} must be in the form: \'container_name.attribute_name\'')
            elif sig.parameters[p].default is not inspect.Parameter.empty:
                raise ValueError(f'Injected parameter: {p} cannot have a default value')
            # TODO: if the parameter has a type annotation, check that the type is the same as the one in the container

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            missing = find_missing_args_and_kwargs_on_func_call(func, *args, **kwargs)
            for missing_param in missing:
                if missing_param in params:
                    p_map = params[missing_param]
                    container_name, attr_name = p_map.split('.')
                    value = containers[container_name][attr_name]   # TODO: handle missing container or attribute

                    # a positional-only argument cannot be passed as kwargs
                    if sig.parameters[missing_param].kind == inspect.Parameter.POSITIONAL_ONLY:
                        args = list(args)
                        args.insert(sig_params.index(missing_param), value)
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
        @inject(y='x.y')
        def foo(x: int) -> int:
            ...


def test_simple_injection_single_arg():
    @inject(x='MyContainer.foo')
    def foo(x: int) -> int:
        return x

    assert foo() == 100


def test_simple_injection_multiple_arg_injection_first():
    @inject(x='MyContainer.foo')
    def foo(x: int, y: int) -> int:
        return x * y

    assert foo(y=2) == 200


def test_simple_injection_multiple_arg_injection_last():
    @inject(y='MyContainer.foo')
    def foo(x: int, y: int) -> int:
        return y // x

    assert foo(25) == 4  # 100 // 25 = 4


def test_injected_parameter_cannot_be_a_kwarg_with_default_in_the_func():
    """
    Because it does not make sense to inject a value that is
    already present in the function signature.
    """
    with pytest.raises(ValueError):

        @inject(y='MyContainer.foo')
        def foo(x: int, y: int = 100) -> int:
            return x * y


def test_invalid_injection_mapping():
    with pytest.raises(ValueError):
        @inject(x='MyContainer')
        def foo(x: int) -> int:
            ...

    with pytest.raises(ValueError):
        @inject(x='MyContainer.')
        def foo(x: int) -> int:
            ...

    with pytest.raises(ValueError):
        @inject(x='MyContainer.foo.bar')
        def foo(x: int) -> int:
            ...


def test_injection_with_multiple_args_when_injected_parameter_is_a_positional_only_arg():
    @inject(x='MyContainer.foo')
    def foo(x: int, /, y: int, z: int) -> int:
        return x + y + z

    assert foo(y=2, z=3) == 105

    assert foo(20, 2, 3) == 25

    assert foo(20, z=5, y=2) == 27

    with pytest.raises(TypeError):
        foo(x=20, y=2, z=3)


def test_cannot_register_container_with_same_name():
    with pytest.raises(ValueError, match='Container with name: MyContainer already registered'):
        @register_container
        class MyContainer:
            ...

