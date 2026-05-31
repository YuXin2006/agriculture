import json
import redis
import logging
from django.conf import settings
from .redis_keys import *
logger = logging.getLogger(__name__)


class RedisClient:
    _instance = None
    
    def __new__(cls):
        """单例模式，使用连接池支持高并发"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 使用连接池，支持高并发场景
            pool = redis.ConnectionPool(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                password=getattr(settings, 'REDIS_PASSWORD', ''),
                decode_responses=True,
                max_connections=200,  # 关键：增加连接池大小，支持高并发
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            cls._instance._client = redis.Redis(connection_pool=pool)
            cls._instance._test_connection()
        return cls._instance
    
    def _test_connection(self):
        """测试Redis连接"""
        try:
            self._client.ping()
            logger.info('Redis connection established successfully')
        except redis.exceptions.RedisError as e:
            logger.error(f'Failed to connect to Redis: {e}')
    
    def _execute(self, func, *args, **kwargs):
        """统一执行方法，处理异常"""
        try:
            return func(*args, **kwargs)
        except redis.exceptions.RedisError as e:
            logger.error(f'Redis operation failed: {e}')
            return None
    
    # ==================== Hash操作 ====================
    
    def hset(self, key, data, expire=None):
        """设置Hash类型数据"""
        result = self._execute(self._client.hset, key, mapping=data)
        if result is not None and expire:
            self._execute(self._client.expire, key, expire)
        return result
    
    def hgetall(self, key):
        """获取Hash类型数据"""
        return self._execute(self._client.hgetall, key)
    
    # ==================== List操作 ====================
    
    def lpush(self, key, data, maxlen=None, expire=None):
        """向列表头部添加数据（支持JSON序列化）"""
        pipeline = self._client.pipeline()#创建redis管道对象，可以执行批量发送多个命令到redis服务器
        pipeline.lpush(key, json.dumps(data))
        if maxlen:
            pipeline.ltrim(key, 0, maxlen - 1)
        if expire:
            pipeline.expire(key, expire)
        return self._execute(pipeline.execute)
    #这里把三个命令(lpush,ltrim,expire)放在一个管道里执行，减少网络往返，提高效率
    def lrange(self, key, start=0, end=-1):
        """获取列表数据（自动JSON反序列化）"""
        result = self._execute(self._client.lrange, key, start, end)
        return [json.loads(item) for item in result] if result else []
    
    # ==================== String操作 ====================
    
    def set(self, key, data, expire=None):
        """设置String类型数据（自动JSON序列化）"""
        return self._execute(
            self._client.set, key, json.dumps(data), ex=expire
        )
    
    def get(self, key):
        """获取String类型数据（自动JSON反序列化）"""
        result = self._execute(self._client.get, key)
        return json.loads(result) if result else None
    
# 全局Redis客户端实例
redis_client = RedisClient()