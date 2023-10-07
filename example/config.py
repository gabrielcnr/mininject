from dataclasses import dataclass

_CONFIG = {
    'development': {
        'redis_url': 'redis://localhost:6379',
    },
    'production': {
        'redis_url': 'redis://somethingelse.supercool:6379',
    },
}

_ENV = None


def set_env(env: str):
    global _ENV
    if _ENV is None:
        _ENV = env
    else:
        raise RuntimeError('Environment already set')


def get_env():
    if _ENV is None:
        raise RuntimeError('Environment not set')
    else:
        return _ENV


@dataclass(frozen=True, kw_only=True)
class ExampleConfig:
    redis_url: str


def create_config_for_environment() -> ExampleConfig:
    env = get_env()
    config = _CONFIG[env]
    return ExampleConfig(redis_url=config['redis_url'])
