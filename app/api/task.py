from flask import request
from flask_restx import Namespace, Resource, fields
from utils.task_manager import task_manager
from utils.logger import logger
from middlewares.auth import auth_required

# 创建命名空间
task_ns = Namespace('task', description='任务管理接口')

# 定义响应模型
task_model = task_ns.model('Task', {
    'task_id': fields.String(description='任务ID'),
    'task_type': fields.String(description='任务类型'),
    'status': fields.String(description='任务状态'),
    'created_at': fields.Integer(description='创建时间'),
    'updated_at': fields.Integer(description='更新时间'),
    'result': fields.Raw(description='任务结果'),
    'error': fields.String(description='错误信息')
})

task_list_model = task_ns.model('TaskList', {
    'total': fields.Integer(description='任务总数'),
    'page': fields.Integer(description='当前页码'),
    'page_size': fields.Integer(description='每页数量'),
    'tasks': fields.List(fields.Nested(task_model), description='任务列表')
})

@task_ns.route('/list')
class TaskList(Resource):
    @task_ns.response(200, '任务列表', task_list_model)
    @auth_required
    def get(self):
        """获取任务列表"""
        try:
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 10, type=int)
            status = request.args.get('status')
            
            # 验证参数
            page = max(1, page)
            page_size = min(50, max(1, page_size))
            
            # 获取任务列表
            task_list = task_manager.get_task_list(page, page_size, status)
            
            return {
                'code': 200,
                'msg': '获取任务列表成功',
                'data': task_list
            }, 200
            
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return {'code': 500, 'msg': '获取任务列表失败', 'data': None}, 200

@task_ns.route('/<task_id>')
class TaskDetail(Resource):
    @task_ns.response(200, '任务详情', task_model)
    @auth_required
    def get(self, task_id):
        """获取任务详情"""
        try:
            task_info = task_manager.get_task(task_id)
            
            if not task_info:
                return {'code': 404, 'msg': '任务不存在', 'data': None}, 200
            
            return {
                'code': 200,
                'msg': '获取任务详情成功',
                'data': task_info
            }, 200
            
        except Exception as e:
            logger.error(f"获取任务详情失败: {e}")
            return {'code': 500, 'msg': '获取任务详情失败', 'data': None}, 200