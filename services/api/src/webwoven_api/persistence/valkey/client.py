"""Minimal typed Redis/Valkey client boundary used by production adapters."""

from typing import Protocol, cast

from redis.asyncio import Redis
from redis.asyncio.client import PubSub


class ValkeySubscription(Protocol):
    async def next_message(self, *, timeout_seconds: float) -> str | None: ...

    async def close(self) -> None: ...


class ValkeyClient(Protocol):
    async def get(self, key: str) -> str | None: ...

    async def set(
        self,
        key: str,
        value: str,
        *,
        ttl_seconds: int,
        only_if_absent: bool = False,
    ) -> bool: ...

    async def compare_delete(self, key: str, expected: str) -> bool: ...

    async def compare_expire(self, key: str, expected: str, ttl_seconds: int) -> bool: ...

    async def expire(self, key: str, ttl_seconds: int) -> None: ...

    async def append_event(
        self,
        stream: str,
        fields: dict[str, str],
        *,
        max_length: int,
    ) -> str: ...

    async def publish(self, channel: str, value: str) -> None: ...

    async def open_subscription(self, channel: str) -> ValkeySubscription: ...

    async def fixed_window_increment(self, key: str, window_seconds: int) -> tuple[int, int]: ...

    async def concurrent_acquire(self, key: str, limit: int, ttl_seconds: int) -> bool: ...

    async def concurrent_release(self, key: str) -> None: ...

    async def ping(self) -> bool: ...

    async def close(self) -> None: ...


class RedisValkeyClient:
    def __init__(self, url: str) -> None:
        self._redis: Redis = Redis.from_url(  # pyright: ignore[reportUnknownMemberType]
            url, decode_responses=True
        )

    async def get(self, key: str) -> str | None:
        value = await self._redis.get(key)
        return cast(str | None, value)

    async def set(
        self,
        key: str,
        value: str,
        *,
        ttl_seconds: int,
        only_if_absent: bool = False,
    ) -> bool:
        result = await self._redis.set(
            key,
            value,
            ex=ttl_seconds,
            nx=only_if_absent,
        )
        return bool(result)

    async def compare_delete(self, key: str, expected: str) -> bool:
        result = await self._redis.eval(
            """
            if redis.call('get', KEYS[1]) == ARGV[1] then
              return redis.call('del', KEYS[1])
            end
            return 0
            """,
            1,
            key,
            expected,
        )
        return int(cast(int, result)) == 1

    async def compare_expire(self, key: str, expected: str, ttl_seconds: int) -> bool:
        result = await self._redis.eval(
            """
            if redis.call('get', KEYS[1]) == ARGV[1] then
              return redis.call('expire', KEYS[1], ARGV[2])
            end
            return 0
            """,
            1,
            key,
            expected,
            ttl_seconds,
        )
        return int(cast(int, result)) == 1

    async def expire(self, key: str, ttl_seconds: int) -> None:
        await self._redis.expire(key, ttl_seconds)

    async def append_event(
        self,
        stream: str,
        fields: dict[str, str],
        *,
        max_length: int,
    ) -> str:
        result = await self._redis.xadd(
            stream,
            fields,  # pyright: ignore[reportArgumentType]
            maxlen=max_length,
            approximate=False,
        )
        return cast(str, result)

    async def publish(self, channel: str, value: str) -> None:
        await self._redis.publish(  # pyright: ignore[reportUnknownMemberType]
            channel, value
        )

    async def open_subscription(self, channel: str) -> ValkeySubscription:
        pubsub = self._redis.pubsub(  # pyright: ignore[reportUnknownMemberType]
            ignore_subscribe_messages=True
        )
        await pubsub.subscribe(channel)
        return RedisValkeySubscription(pubsub)

    async def fixed_window_increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        result = await self._redis.eval(
            """
            local current = redis.call('incr', KEYS[1])
            if current == 1 then
              redis.call('expire', KEYS[1], ARGV[1])
            end
            local ttl = redis.call('ttl', KEYS[1])
            return {current, ttl}
            """,
            1,
            key,
            window_seconds,
        )
        values = cast(list[int], result)
        return int(values[0]), max(int(values[1]), 0)

    async def concurrent_acquire(self, key: str, limit: int, ttl_seconds: int) -> bool:
        result = await self._redis.eval(
            """
            local current = redis.call('incr', KEYS[1])
            if current > tonumber(ARGV[1]) then
              redis.call('decr', KEYS[1])
              return 0
            end
            redis.call('expire', KEYS[1], ARGV[2])
            return 1
            """,
            1,
            key,
            limit,
            ttl_seconds,
        )
        return int(cast(int, result)) == 1

    async def concurrent_release(self, key: str) -> None:
        await self._redis.eval(
            """
            local current = tonumber(redis.call('get', KEYS[1]) or '0')
            if current <= 1 then
              redis.call('del', KEYS[1])
              return 0
            end
            return redis.call('decr', KEYS[1])
            """,
            1,
            key,
        )

    async def ping(self) -> bool:
        try:
            return bool(
                await self._redis.ping()  # pyright: ignore[reportUnknownMemberType]
            )
        except Exception:
            return False

    async def close(self) -> None:
        await self._redis.aclose()


class RedisValkeySubscription:
    def __init__(self, pubsub: PubSub) -> None:
        self._pubsub = pubsub

    async def next_message(self, *, timeout_seconds: float) -> str | None:
        message = cast(
            dict[str, object] | None,
            await self._pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=timeout_seconds,
            ),
        )
        if message is None:
            return None
        data = message.get("data")
        return data if isinstance(data, str) else None

    async def close(self) -> None:
        await self._pubsub.aclose()
