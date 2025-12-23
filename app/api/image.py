from flask import request
from flask_restx import Namespace, Resource, fields
from utils.model_scheduler import model_scheduler
from utils.task_manager import task_manager
from utils.logger import logger
from middlewares.auth import auth_required
import uuid
import os
import base64
from PIL import Image
import io

# 创建命名空间
image_ns = Namespace('image', description='图片生成接口')

# 定义请求模型
text2img_model = image_ns.model('Text2ImgRequest', {
    'prompt': fields.String(required=True, description='生成提示词'),
    'negative_prompt': fields.String(required=False, description='负面提示词'),
    'seed': fields.Integer(required=False, description='随机种子'),
    'steps': fields.Integer(required=False, default=50, description='推理步数'),
    'width': fields.Integer(required=False, default=512, description='图片宽度'),
    'height': fields.Integer(required=False, default=512, description='图片高度')
})

img2img_model = image_ns.model('Img2ImgRequest', {
    'prompt': fields.String(required=True, description='生成提示词'),
    'negative_prompt': fields.String(required=False, description='负面提示词'),
    'image': fields.String(required=True, description='输入图片的base64编码'),
    'seed': fields.Integer(required=False, description='随机种子'),
    'steps': fields.Integer(required=False, default=50, description='推理步数')
})

@image_ns.route('/text2img')
class Text2Img(Resource):
    @image_ns.expect(text2img_model)
    @image_ns.response(200, '生成请求已提交')
    @auth_required
    def post(self):
        """文生图接口"""
        try:
            data = request.get_json()
            prompt = data.get('prompt')
            negative_prompt = data.get('negative_prompt', '')
            seed = data.get('seed')
            steps = data.get('steps', 50)
            width = data.get('width', 512)
            height = data.get('height', 512)
            
            # 验证参数
            if not prompt:
                return {'code': 400, 'msg': '缺少提示词参数', 'data': None}, 200
            
            # 创建任务
            task_params = {
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'seed': seed,
                'steps': steps,
                'width': width,
                'height': height
            }
            
            task_id = task_manager.create_task('text2img', task_params)
            
            return {
                'code': 200,
                'msg': '文生图请求已提交',
                'data': {'task_id': task_id}
            }, 200
            
        except Exception as e:
            logger.error(f"文生图请求失败: {e}")
            return {'code': 500, 'msg': '文生图请求失败', 'data': None}, 200

@image_ns.route('/img2img')
class Img2Img(Resource):
    @image_ns.expect(img2img_model)
    @image_ns.response(200, '生成请求已提交')
    @auth_required
    def post(self):
        """图生图接口"""
        try:
            data = request.get_json()
            prompt = data.get('prompt')
            negative_prompt = data.get('negative_prompt', '')
            image_base64 = data.get('image')
            seed = data.get('seed')
            steps = data.get('steps', 50)
            
            # 验证参数
            if not prompt:
                return {'code': 400, 'msg': '缺少提示词参数', 'data': None}, 200
            if not image_base64:
                return {'code': 400, 'msg': '缺少图片参数', 'data': None}, 200
            
            # 创建任务
            task_params = {
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'image': image_base64,
                'seed': seed,
                'steps': steps
            }
            
            task_id = task_manager.create_task('img2img', task_params)
            
            return {
                'code': 200,
                'msg': '图生图请求已提交',
                'data': {'task_id': task_id}
            }, 200
            
        except Exception as e:
            logger.error(f"图生图请求失败: {e}")
            return {'code': 500, 'msg': '图生图请求失败', 'data': None}, 200

@image_ns.route('/result/<task_id>')
class ImageResult(Resource):
    @image_ns.response(200, '任务结果')
    @auth_required
    def get(self, task_id):
        """获取图片生成任务结果"""
        try:
            task_info = task_manager.get_task(task_id)
            
            if not task_info:
                return {'code': 404, 'msg': '任务不存在', 'data': None}, 200
            
            return {
                'code': 200,
                'msg': '获取任务结果成功',
                'data': {
                    'task_id': task_id,
                    'status': task_info['status'],
                    'result': task_info['result'],
                    'error': task_info['error']
                }
            }, 200
            
        except Exception as e:
            logger.error(f"获取图片生成结果失败: {e}")
            return {'code': 500, 'msg': '获取任务结果失败', 'data': None}, 200