from flask import request
from flask_restx import Namespace, Resource, fields
from utils.task_manager import task_manager
from utils.logger import logger
from middlewares.auth import auth_required
from utils.lora_utils import validate_lora_ids, validate_lora_files

# 创建命名空间
image_ns = Namespace('image', description='图片生成接口')

# 定义请求模型
text2img_model = image_ns.model('Text2ImgRequest', {
    'prompt': fields.String(required=True, description='生成提示词'),
    'negative_prompt': fields.String(required=False, description='负面提示词'),
    'seed': fields.Integer(required=False, description='随机种子'),
    'steps': fields.Integer(required=False, default=9, description='推理步数'),
    'width': fields.Integer(required=False, default=544, description='图片宽度'),
    'height': fields.Integer(required=False, default=544, description='图片高度'),
    'guidance_scale': fields.Float(required=False, default=7.5, description='引导缩放因子'),
    'lora_ids': fields.List(fields.Integer, required=False, description='LoRA模型ID列表')
})

img2img_model = image_ns.model('Img2ImgRequest', {
    'prompt': fields.String(required=True, description='生成提示词'),
    'negative_prompt': fields.String(required=False, description='负面提示词'),
    'seed': fields.Integer(required=False, description='随机种子'),
    'steps': fields.Integer(required=False, default=20, description='推理步数'),
    'width': fields.Integer(required=False, default=544, description='图片宽度'),
    'height': fields.Integer(required=False, default=544, description='图片高度'),
    'guidance_scale': fields.Float(required=False, default=7.5, description='引导缩放因子'),
    'image_path': fields.String(required=True, description='输入图片在服务器上的路径'),
    'lora_ids': fields.List(fields.Integer, required=False, description='LoRA模型ID列表')
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
            steps = data.get('steps', 9)
            width = data.get('width', 544)
            height = data.get('height', 544)
            guidance_scale = data.get('guidance_scale', 7.5)
            
            # 未知bug 反向提示词必须要和提示词一样，不然画面9步快速推理会有问题 
            negative_prompt = prompt
            
            # 验证参数
            if not prompt:
                return {'code': 400, 'msg': '缺少提示词参数', 'data': None}, 200
            
            # 校验lora_ids
            lora_ids = data.get('lora_ids', [])
            if lora_ids:
                # 校验lora_id是否存在于配置文件中
                valid, msg = validate_lora_ids('text2img', lora_ids)
                if not valid:
                    return {'code': 400, 'msg': msg, 'data': None}, 200
                
                # 校验lora文件是否存在
                valid, msg = validate_lora_files('text2img', lora_ids)
                if not valid:
                    return {'code': 400, 'msg': msg, 'data': None}, 200
            
            # 创建任务
            task_params = {
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'seed': seed,
                'steps': steps,
                'width': width,
                'height': height,
                'guidance_scale': guidance_scale,
                'lora_ids': lora_ids
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
            image_path = data.get('image_path')
            seed = data.get('seed')
            steps = data.get('steps', 20)
            width = data.get('width', 544)
            height = data.get('height', 544)
            guidance_scale = data.get('guidance_scale', 7.5)

            negative_prompt = negative_prompt.strip() if (negative_prompt and negative_prompt.strip()) else '模糊, 低分辨率, 像素化, 马赛克, 透视错误, 背景扭曲, 漂浮物体, 物体融合, 重复物体, 背景杂乱, 过曝, 欠曝, 光线不自然, 阴影不一致, 色彩溢出, 色彩失真, 诡异配色, 边缘模糊, 锯齿边缘, 文字叠加, 水印, 签名, AI伪影, 画面错乱, 噪点, 颗粒感, 物体畸形, 材质不真实, 构图混乱, 元素杂乱, 人物变形, 面部扭曲, 五官错位, 多手指, 少手指, 手指扭曲, 头发杂乱, 服装穿模, 身体比例失调, 动作僵硬, 表情诡异, 皮肤质感差, 细节丢失'
            
            # 验证参数
            if not prompt:
                return {'code': 400, 'msg': '缺少提示词参数', 'data': None}, 200
            if not image_path:
                return {'code': 400, 'msg': '缺少图片路径参数', 'data': None}, 200
            
            # 校验lora_ids
            lora_ids = data.get('lora_ids', [])
            if lora_ids:
                # 校验lora_id是否存在于配置文件中
                valid, msg = validate_lora_ids('img2img', lora_ids)
                if not valid:
                    return {'code': 400, 'msg': msg, 'data': None}, 200
                
                # 校验lora文件是否存在
                valid, msg = validate_lora_files('img2img', lora_ids)
                if not valid:
                    return {'code': 400, 'msg': msg, 'data': None}, 200
            
            # 创建任务
            task_params = {
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'image_path': image_path,
                'seed': seed,
                'steps': steps,
                'width': width,
                'height': height,
                'guidance_scale': guidance_scale,
                'lora_ids': lora_ids
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