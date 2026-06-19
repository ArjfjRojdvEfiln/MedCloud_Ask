import hashlib
import redis.asyncio as redis
from app.core.redis_client import redis_client


class RedisBloomFilter:
    """基于 Redis 位图手写的布隆过滤器，用 SETBIT/GETBIT 读写一个 bit 数组。"""

    def __init__(self, client: redis.Redis, key: str,
                 bit_size: int = 1 << 20, hash_count: int = 7):
        self.client = client
        self.key = key                 # Redis 里存位图的 key
        self.bit_size = bit_size       # m：位数组总长度
        self.hash_count = hash_count   # k：哈希函数个数

    def _positions(self, value: str) -> list[int]:
        """双哈希技巧：用 2 个基础哈希拼出 k 个位置，避免引入 mmh3 这类 C 扩展"""
        digest = hashlib.sha256(value.encode("utf-8")).digest()
        h1 = int.from_bytes(digest[:8], "big")
        h2 = int.from_bytes(digest[8:16], "big")
        # g_i(x) = (h1 + i * h2) % m，一次哈希就能派生出 k 个位置
        return [(h1 + i * h2) % self.bit_size for i in range(self.hash_count)]

    async def add(self, value: str) -> None:
        """把这个值的 k 个位置全部置 1（用 pipeline 一次往返，省网络开销）"""
        positions = self._positions(value)
        async with self.client.pipeline(transaction=False) as pipe:
            for pos in positions:
                pipe.setbit(self.key, pos, 1)
            await pipe.execute()

    async def exists(self, value: str) -> bool:
        """只要有一位是 0，就一定不存在；全是 1，才说"可能存在"""
        positions = self._positions(value)
        async with self.client.pipeline(transaction=False) as pipe:
            for pos in positions:
                pipe.getbit(self.key, pos)
            bits = await pipe.execute()
        return all(bits)   # bits 是一串 0/1，all() 全为 1 才 True

# 机构 slug 专用的布隆过滤器实例，全应用共用
org_bloom = RedisBloomFilter(redis_client, key="bloom:org_slugs")