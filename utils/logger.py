import logging
import os
from logging.handlers import RotatingFileHandler
from config.config import config

# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 日志格式
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(process)d - %(threadName)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 创建日志记录器
def setup_logger(name=__name__, level=logging.INFO):
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器（带轮换）
        log_file = os.path.join(log_dir, 'app.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5  # 保留5个备份文件
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有调试信息
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# 创建默认日志记录器
logger = setup_logger()

# 错误日志记录函数
def log_error(error, module_name=None, extra_info=None):
    """记录错误信息"""
    log_msg = f"Error: {str(error)}"
    if module_name:
        log_msg = f"[{module_name}] {log_msg}"
    if extra_info:
        log_msg = f"{log_msg} | Extra: {extra_info}"
    logger.error(log_msg, exc_info=True)

# 调试日志记录函数
def log_debug(message, module_name=None):
    """记录调试信息"""
    log_msg = message
    if module_name:
        log_msg = f"[{module_name}] {log_msg}"
    logger.debug(log_msg)

# 信息日志记录函数
def log_info(message, module_name=None):
    """记录信息"""
    log_msg = message
    if module_name:
        log_msg = f"[{module_name}] {log_msg}"
    logger.info(log_msg)

# 警告日志记录函数
def log_warning(message, module_name=None):
    """记录警告"""
    log_msg = message
    if module_name:
        log_msg = f"[{module_name}] {log_msg}"
    logger.warning(log_msg)