from fakeredis import FakeRedis


def create_redis_client(redis_url: str) -> FakeRedis:
    return FakeRedis(redis_url)


class Database(object):

    def __init__(self, redis_client):
        self.redis_client = redis_client

    def get(self, key):
        return self.redis_client.get(key)

    def set(self, key, value):
        return self.redis_client.set(key, value)

    def get_all(self):
        keys = self.redis_client.keys()
        return {key: self.redis_client.get(key) for key in keys}
