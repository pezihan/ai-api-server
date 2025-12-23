from flask import request
from flask_restx import Namespace, Resource, fields
from middlewares.auth import auth_required
from utils.logger import logger
import os
import uuid
import time

# 创建命名空间
upload_ns = Namespace('upload', description='文件上传接口')

# 文件上传目录配置
UPLOAD_DIR = '/tmp/ai-api-uploads'
# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 允许的图片和视频文件类型
ALLOWED_IMAGE_TYPES = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_TYPES = {'mp4', 'avi', 'mov', 'mkv'}

# 定义响应模型
upload_response_model = upload_ns.model('UploadResponse', {
    'code': fields.Integer(description='业务状态码'),
    'msg': fields.String(description='消息'),
    'data': fields.Nested({
        'file_path': fields.String(description='文件在服务器上的路径'),
        'file_name': fields.String(description='文件名'),
        'file_size': fields.Integer(description='文件大小（字节）'),
        'upload_time': fields.Integer(description='上传时间戳')
    })
})

@upload_ns.route('/')
class UploadFile(Resource):
    """文件上传接口"""
    
    @upload_ns.expect(
        upload_ns.parser()
        .add_argument('file', type='file', location='files', required=True, help='要上传的文件')
    )
    @upload_ns.response(200, '上传成功', upload_response_model)
    @auth_required
    def post(self):
        """
        上传文件到服务器
        
        支持上传图片和视频文件
        """
        try:
            # 获取上传的文件
            file = request.files['file']
            if not file or file.filename == '':
                return {
                    'code': 400,
                    'msg': '未选择文件',
                    'data': None
                }, 200
            
            # 检查文件类型
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if file_ext not in ALLOWED_IMAGE_TYPES and file_ext not in ALLOWED_VIDEO_TYPES:
                return {
                    'code': 400,
                    'msg': '不支持的文件类型，仅支持图片(png,jpg,jpeg,gif)和视频(mp4,avi,mov,mkv)',
                    'data': None
                }, 200
            
            # 生成唯一的文件名
            timestamp = int(time.time())
            unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_ext}"
            
            # 保存文件
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            file.save(file_path)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            logger.info(f"文件上传成功: {file.filename} -> {unique_filename}, 大小: {file_size} bytes")
            
            return {
                'code': 200,
                'msg': '文件上传成功',
                'data': {
                    'file_path': file_path,
                    'file_name': unique_filename,
                    'file_size': file_size,
                    'upload_time': timestamp
                }
            }, 200
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return {
                'code': 500,
                'msg': '文件上传失败',
                'data': None
            }, 200
