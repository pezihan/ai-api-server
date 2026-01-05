import pika
import time
from functools import wraps
from config.config import config
from utils.logger import logger, log_error
import threading

class RabbitMQClient:
    """RabbitMQ客户端单例类"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RabbitMQClient, cls).__new__(cls)
                cls._instance.connection = None
                cls._instance.channel = None
                cls._instance.connection_params = None
                # 启动时初始化连接
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        """初始化RabbitMQ连接，带重联机制"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 关闭现有连接和通道
                self._close_connection()
                
                # 创建连接参数
                credentials = pika.PlainCredentials(
                    config.RABBITMQ_USERNAME,
                    config.RABBITMQ_PASSWORD
                )
                self.connection_params = pika.ConnectionParameters(
                    host=config.RABBITMQ_HOST,
                    port=config.RABBITMQ_PORT,
                    virtual_host=config.RABBITMQ_VIRTUAL_HOST,
                    credentials=credentials,
                    socket_timeout=5
                )
                
                # 建立连接
                self.connection = pika.BlockingConnection(self.connection_params)
                self.channel = self.connection.channel()
                
                logger.info(f"RabbitMQ连接成功: {config.RABBITMQ_HOST}:{config.RABBITMQ_PORT} (尝试次数: {attempt + 1})")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"RabbitMQ连接失败 (尝试 {attempt + 1}/{max_retries}), 将在 {retry_delay} 秒后重试: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # 指数退避
                else:
                    log_error(e, "RabbitMQClient")
                    logger.error(f"RabbitMQ连接失败，已达到最大重试次数 ({max_retries})")
                    raise ConnectionError(f"无法连接到RabbitMQ: {str(e)}")
    
    def _close_connection(self):
        """安全关闭连接和通道"""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and self.connection.is_open:
                self.connection.close()
        except Exception as e:
            logger.warning(f"关闭RabbitMQ连接时出错: {str(e)}")
    
    def _reconnect_wrapper(func):
        """重连装饰器"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                # 检查连接是否有效
                if not self.connection or self.connection.is_closed or not self.channel or self.channel.is_closed:
                    logger.warning("RabbitMQ连接已关闭，尝试重新连接")
                    self._initialize()
                return func(self, *args, **kwargs)
            except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError, ConnectionError) as e:
                logger.warning(f"RabbitMQ连接异常，尝试重新连接: {str(e)}")
                self._initialize()
                return func(self, *args, **kwargs)
            except Exception as e:
                log_error(e, "RabbitMQClient", f"{func.__name__} {args} {kwargs}")
                raise
        return wrapper
    
    @_reconnect_wrapper
    def declare_queue(self, queue_name, durable=False):
        """声明队列"""
        self.channel.queue_declare(queue=queue_name, durable=durable)
        logger.info(f"队列声明成功: {queue_name}")
    
    @_reconnect_wrapper
    def publish_message(self, queue_name, message, durable=False):
        """发布消息到队列"""
        # 确保队列存在
        self.declare_queue(queue_name, durable)
        
        # 发布消息
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # 持久化消息
            ) if durable else None
        )
        logger.info(f"消息发布成功: 队列={queue_name}, 消息={message[:50]}...")
    
    @_reconnect_wrapper
    def consume_messages(self, queue_name, callback, durable=False):
        """消费队列消息"""
        # 确保队列存在
        self.declare_queue(queue_name, durable)
        
        # 设置每次只接收一条消息，确认后再接收下一条
        self.channel.basic_qos(prefetch_count=1)
        
        # 开始消费
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        
        logger.info(f"开始消费消息: {queue_name}")
        self.channel.start_consuming()
    
    def stop_consuming(self):
        """停止消息消费"""
        try:
            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
                logger.info("已停止消息消费")
        except Exception as e:
            logger.warning(f"停止消息消费时出错: {str(e)}")
    
    @_reconnect_wrapper
    def basic_ack(self, delivery_tag, multiple=False):
        """确认消息"""
        try:
            if self.channel and self.channel.is_open:
                self.channel.basic_ack(delivery_tag=delivery_tag, multiple=multiple)
                logger.info(f"消息确认成功: delivery_tag={delivery_tag}")
            else:
                logger.warning("通道已关闭，无法执行ack操作")
        except Exception as e:
            log_error(e, "RabbitMQClient", f"basic_ack delivery_tag={delivery_tag}")
            raise
    
    @_reconnect_wrapper
    def basic_nack(self, delivery_tag, multiple=False, requeue=True):
        """拒绝消息"""
        try:
            if self.channel and self.channel.is_open:
                self.channel.basic_nack(delivery_tag=delivery_tag, multiple=multiple, requeue=requeue)
                logger.info(f"消息拒绝成功: delivery_tag={delivery_tag}, requeue={requeue}")
            else:
                logger.warning("通道已关闭，无法执行nack操作")
        except Exception as e:
            log_error(e, "RabbitMQClient", f"basic_nack delivery_tag={delivery_tag}")
            raise
    
    def close(self):
        """关闭连接"""
        try:
            # 先停止消费
            self.stop_consuming()
            
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and self.connection.is_open:
                self.connection.close()
            logger.info("RabbitMQ连接已关闭")
        except Exception as e:
            log_error(e, "RabbitMQClient", "close")

# 创建RabbitMQ客户端实例
rabbitmq_client = RabbitMQClient()