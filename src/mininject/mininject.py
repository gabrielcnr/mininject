import functools
import inspect

from mininject import Injectable

from .injectable import _get_injected_value_from_container  # TODO: fix this


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
            missing = _find_missing_args_and_kwargs_on_func_call(func, *args, **kwargs)
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


def _find_missing_args_and_kwargs_on_func_call(func, *args, **kwargs):
    sig = inspect.signature(func)
    bound = sig.bind_partial(*args, **kwargs)
    missing = [param for param in sig.parameters.values()
               if (param.name not in bound.arguments and param.default == param.empty)]
    return [m.name for m in missing]


