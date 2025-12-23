from flask_restx import Namespace, Resource

# 创建命名空间
health_ns = Namespace('health', description='健康检查接口')

# 健康检查接口
@health_ns.route('')
class HealthCheck(Resource):
    """健康检查接口"""
    @health_ns.response(200, '服务状态')
    def get(self):
        """健康检查接口"""
        return {
            'code': 200,
            'msg': '服务正常',
            'data': {
                'status': 'ok',
                'service': 'AI API Server'
            }
        }, 200
