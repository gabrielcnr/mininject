from redis import Redis

from example.component import Database, create_redis_client
from example.config import create_config_for_environment, ExampleConfig
from mininject import Container, Injectable


class ExampleContainer(Container):
    """ type hints are meaningful after container initialization """
    config: ExampleConfig = Injectable(create_config_for_environment)

    redis_client: Redis = Injectable(create_redis_client, config.redis_url)

    cache: Database = Injectable(Database, redis_client)
