from flask import request
from flask_restx import Namespace, Resource, fields
from utils.logger import logger, log_error
from middlewares.auth import auth_middleware

# 创建命名空间
auth_ns = Namespace('auth', description='认证相关接口')

# 定义模型
login_model = auth_ns.model('Login', {
    'password': fields.String(required=True, description='登录密码')
})

# 登录接口
@auth_ns.route('/login')
class Login(Resource):
    """登录接口，只需要密码验证"""
    @auth_ns.expect(login_model)
    @auth_ns.response(200, '登录结果')
    def post(self):
        """登录接口，只需要密码验证"""
        try:
            data = request.get_json()
            if not data or 'password' not in data:
                logger.warning("登录请求缺少密码参数")
                return {
                    'code': 400,
                    'msg': '缺少密码参数',
                    'data': None
                }, 200
            
            password = data['password']
            result = auth_middleware.login(password)
            
            if result['success']:
                return {
                    'code': 200,
                    'msg': '登录成功',
                    'data': {
                        'token': result['token']
                    }
                }, 200
            else:
                return {
                    'code': 401,
                    'msg': result['message'],
                    'data': None
                }, 200
                
        except Exception as e:
            log_error(e, "FlaskApp", "Login API")
            return {
                'code': 500,
                'msg': '登录过程中发生错误',
                'data': None
            }, 200
