import jwt
import time
from functools import wraps
from flask import request
from config.config import config
from utils.logger import logger, log_error

# JWT配置

class AuthMiddleware:
    """认证中间件类"""
    
    @staticmethod
    def generate_token():
        """生成JWT令牌（无过期时间）"""
        try:
            payload = {
                'iat': time.time()
            }
            token = jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')
            return token
        except Exception as e:
            log_error(e, "AuthMiddleware", "generate_token")
            raise
    
    @staticmethod
    def verify_token(token):
        """验证JWT令牌（忽略过期检查）"""
        try:
            # 验证token签名，忽略过期检查
            jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'], options={"verify_exp": False})
            return True
        except jwt.InvalidTokenError:
            logger.warning("无效的Token")
            return False
        except Exception as e:
            log_error(e, "AuthMiddleware", "verify_token")
            return False
    
    @staticmethod
    def login_required(f):
        """登录验证装饰器"""
        @wraps(f)
        def decorated(*args, **kwargs):
            # 跳过OPTIONS请求的认证检查，因为OPTIONS请求是预检请求，不包含Authorization头
            if request.method == 'OPTIONS':
                return f(*args, **kwargs)
            
            token = request.headers.get('Authorization')
            
            if not token:
                return {
                    'code': 401,
                    'msg': '缺少认证令牌',
                    'data': None
                }, 200
            
            # 移除Bearer前缀
            if token.startswith('Bearer '):
                token = token[7:]
            
            # 验证令牌
            if not AuthMiddleware.verify_token(token):
                return {
                    'code': 401,
                    'msg': '认证令牌无效或已过期',
                    'data': None
                }, 200
            
            return f(*args, **kwargs)
        
        return decorated
    
    @staticmethod
    def login(password):
        """登录验证"""
        try:
            if password == config.LOGIN_PASSWORD:
                token = AuthMiddleware.generate_token()
                logger.info("登录成功")
                return {
                    'success': True,
                    'token': token
                }
            else:
                logger.warning("登录失败：密码错误")
                return {
                    'success': False,
                    'message': '密码错误'
                }
        except Exception as e:
            log_error(e, "AuthMiddleware", "login")
            return {
                'success': False,
                'message': '登录过程中发生错误'
            }

# 创建认证中间件实例
auth_middleware = AuthMiddleware()

# 提供auth_required作为login_required的别名，保持兼容性
auth_required = AuthMiddleware.login_required