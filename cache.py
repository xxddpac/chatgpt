import aioredis
import json
from utils import *


async def connect_redis():
    redis = await aioredis.create_redis_pool((redis_host, redis_port), encoding=redis_charset, db=redis_db)
    return redis


# 为了节省chat_gpt关联上下文消耗token数
# 使用过期的定长队列来缓存上下文
# 每个企业微信用户只关联最近6次会话历史,缓存时间60分钟
async def enqueue(key, value):
    redis = await connect_redis()
    try:
        remaining_ttl = await redis.ttl(key)
        if remaining_ttl < 0:
            await redis.delete(key)
        await redis.rpush(key, value)
        current_length = await redis.llen(key)
        if current_length >= redis_queue_max_length:
            elements_to_remove = current_length - redis_queue_max_length
            await redis.ltrim(key, elements_to_remove, -1)
        await redis.expire(key, redis_queue_ttl)
    finally:
        redis.close()
        await redis.wait_closed()


async def dequeue(key):
    redis = await connect_redis()
    try:
        result = await redis.lrange(key, 0, -1)
        return [json.loads(item) for item in result]
    finally:
        redis.close()
        await redis.wait_closed()
