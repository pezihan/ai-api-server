import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    # 服务配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # 登录密码配置
    LOGIN_PASSWORD = os.environ.get('LOGIN_PASSWORD', 'default-password')
    
    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # RabbitMQ配置
    RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
    RABBITMQ_USERNAME = os.environ.get('RABBITMQ_USERNAME', 'guest')
    RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', 'guest')
    RABBITMQ_VIRTUAL_HOST = os.environ.get('RABBITMQ_VIRTUAL_HOST', '/')

    # 配置文件目录
    CONFIG_DIR = os.path.dirname(__file__)

    # 文件保存目录
    FILE_SAVE_DIR = os.environ.get('FILE_SAVE_DIR', '/files')

    # wan模型目录
    MODEL_DIR = os.environ.get('MODEL_DIR', '/models')
    WAN_MODEL_CONFIG_DIR = os.environ.get('WAN_MODEL_CONFIG_DIR', os.path.join(CONFIG_DIR, os.environ.get('WAN_TYPE', 'wan')))
    
    LORA_DIR = os.environ.get('LORA_DIR', '/loras')
# 创建配置实例
config = Config()