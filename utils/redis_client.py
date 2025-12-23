import redis
from redis.exceptions import ConnectionError as RedisConnectionError
from config.config import config
from utils.logger import logger, log_error
import time
from functools import wraps

class RedisClient:
    """Redis客户端单例类，支持启动时连接和重联机制"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化Redis连接，带重联机制"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 配置连接池和重试机制
                self.client = redis.Redis(
                    host=config.REDIS_HOST,
                    port=config.REDIS_PORT,
                    password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
                    db=config.REDIS_DB,
                    decode_responses=True,  # 自动解码为字符串
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    retry_on_error=[RedisConnectionError],
                    health_check_interval=30  # 30秒健康检查一次
                )
                # 测试连接
                self.client.ping()
                logger.info(f"Redis连接成功: {config.REDIS_HOST}:{config.REDIS_PORT} (尝试次数: {attempt + 1})")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Redis连接失败 (尝试 {attempt + 1}/{max_retries}), 将在 {retry_delay} 秒后重试: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # 指数退避
                else:
                    log_error(e, "RedisClient")
                    logger.error(f"Redis连接失败，已达到最大重试次数 ({max_retries})")
                    raise ConnectionError(f"无法连接到Redis: {str(e)}")
    
    def _reconnect_wrapper(func):
        """重连装饰器"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except (RedisConnectionError, ConnectionError) as e:
                logger.warning(f"Redis连接丢失，尝试重新连接: {str(e)}")
                # 重新初始化连接
                self._initialize()
                # 再次尝试执行原函数
                return func(self, *args, **kwargs)
            except Exception as e:
                log_error(e, "RedisClient", f"{func.__name__} {args} {kwargs}")
                raise
        return wrapper
    
    @_reconnect_wrapper
    def get(self, key):
        """获取键值"""
        return self.client.get(key)
    
    @_reconnect_wrapper
    def set(self, key, value, ex=None):
        """设置键值，可选过期时间"""
        return self.client.set(key, value, ex=ex)
    
    @_reconnect_wrapper
    def delete(self, key):
        """删除键"""
        return self.client.delete(key)
    
    @_reconnect_wrapper
    def exists(self, key):
        """检查键是否存在"""
        return self.client.exists(key)
    
    @_reconnect_wrapper
    def keys(self, pattern="*"):
        """获取匹配模式的所有键"""
        return self.client.keys(pattern)
    
    @_reconnect_wrapper
    def expire(self, key, time):
        """设置键过期时间"""
        return self.client.expire(key, time)
    
    @_reconnect_wrapper
    def ttl(self, key):
        """获取键剩余过期时间"""
        return self.client.ttl(key)

# 创建Redis客户端实例
redis_client = RedisClient()