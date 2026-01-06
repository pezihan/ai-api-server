from flask import request
from flask_restx import Namespace, Resource, fields
from utils.task_manager import task_manager
from utils.logger import logger
from middlewares.auth import auth_required

# 创建命名空间
video_ns = Namespace('video', description='视频生成接口')

# 定义请求模型
text2video_model = video_ns.model('Text2VideoRequest', {
    'prompt': fields.String(required=True, description='生成提示词'),
    'negative_prompt': fields.String(required=False, description='负面提示词'),
    'seed': fields.Integer(required=False, description='随机种子'),
    'steps': fields.Integer(required=False, default=4, description='推理步数'),
    'width': fields.Integer(required=False, default=544, description='视频宽度'),
    'height': fields.Integer(required=False, default=960, description='视频高度'),
    'num_frames': fields.Integer(required=False, default=81, description='视频帧数')
})

img2video_model = video_ns.model('Img2VideoRequest', {
    'prompt': fields.String(required=True, description='生成提示词'),
    'negative_prompt': fields.String(required=False, description='负面提示词'),
    'image_path': fields.String(required=True, description='输入图片在服务器上的路径'),
    'seed': fields.Integer(required=False, description='随机种子'),
    'steps': fields.Integer(required=False, default=4, description='推理步数'),
    'width': fields.Integer(required=False, default=544, description='视频宽度'),
    'height': fields.Integer(required=False, default=960, description='视频高度'),
    'num_frames': fields.Integer(required=False, default=81, description='视频帧数')
})

@video_ns.route('/text2video')
class Text2Video(Resource):
    @video_ns.expect(text2video_model)
    @video_ns.response(200, '生成请求已提交')
    @auth_required
    def post(self):
        """文生视频接口"""
        try:
            data = request.get_json()
            prompt = data.get('prompt')
            negative_prompt = data.get('negative_prompt', '')
            seed = data.get('seed')
            steps = data.get('steps', 4)
            width = data.get('width', 544)
            height = data.get('height', 960)
            num_frames = data.get('num_frames', 81)
            
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
                'height': height,
                'num_frames': num_frames
            }
            
            task_id = task_manager.create_task('text2video', task_params)
            
            return {
                'code': 200,
                'msg': '文生视频请求已提交',
                'data': {'task_id': task_id}
            }, 200
            
        except Exception as e:
            logger.error(f"文生视频请求失败: {e}")
            return {'code': 500, 'msg': '文生视频请求失败', 'data': None}, 200

@video_ns.route('/img2video')
class Img2Video(Resource):
    @video_ns.expect(img2video_model)
    @video_ns.response(200, '生成请求已提交')
    @auth_required
    def post(self):
        """图生视频接口"""
        try:
            data = request.get_json()
            prompt = data.get('prompt')
            negative_prompt = data.get('negative_prompt', '')
            image_path = data.get('image_path')
            seed = data.get('seed')
            steps = data.get('steps', 4)
            width = data.get('width', 544)
            height = data.get('height', 960)
            num_frames = data.get('num_frames', 81)
            
            # 验证参数
            if not prompt:
                return {'code': 400, 'msg': '缺少提示词参数', 'data': None}, 200
            if not image_path:
                return {'code': 400, 'msg': '缺少图片路径参数', 'data': None}, 200
            
            # 创建任务
            task_params = {
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'image_path': image_path,
                'seed': seed,
                'steps': steps,
                'width': width,
                'height': height,
                'num_frames': num_frames
            }
            
            task_id = task_manager.create_task('img2video', task_params)
            
            return {
                'code': 200,
                'msg': '图生视频请求已提交',
                'data': {'task_id': task_id}
            }, 200
            
        except Exception as e:
            logger.error(f"图生视频请求失败: {e}")
            return {'code': 500, 'msg': '图生视频请求失败', 'data': None}, 200

@video_ns.route('/result/<task_id>')
class VideoResult(Resource):
    @video_ns.response(200, '任务结果')
    @auth_required
    def get(self, task_id):
        """获取视频生成任务结果"""
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
            logger.error(f"获取视频生成结果失败: {e}")
            return {'code': 500, 'msg': '获取任务结果失败', 'data': None}, 200