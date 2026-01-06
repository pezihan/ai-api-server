from flask import Flask, request, send_from_directory
from flask_cors import CORS
from flask_restx import Api
from config.config import config
from utils.logger import logger, log_error
import traceback

# 导入API模块的命名空间
from app.api import auth_ns, health_ns, image_ns, video_ns, task_ns, upload_ns

# 创建Flask应用
app = Flask(__name__)

# 配置CORS，允许所有来源，处理预检请求
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Length"],
        "supports_credentials": True
    }
})

# 创建API对象
api = Api(
    app,
    version='1.0',
    title='AI API Server',
    description='AI API服务接口文档',
    doc='/api/docs',  # 文档访问路径
    prefix='/api'  # API前缀
)

# 注册命名空间
api.add_namespace(auth_ns)
api.add_namespace(health_ns)
api.add_namespace(image_ns)
api.add_namespace(video_ns)
api.add_namespace(task_ns)
api.add_namespace(upload_ns)

# 请求日志记录中间件
@app.before_request
def log_request_info():
    """记录请求信息"""
    logger.info(
        f"Request: {request.method} {request.path} | IP: {request.remote_addr} | "
        f"User-Agent: {request.headers.get('User-Agent')}"
    )

# 全局错误处理
@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理"""
    log_error(e, "FlaskApp", f"Path: {request.path}, Method: {request.method}")
    return {
        'code': 500,
        'msg': '服务器内部错误',
        'data': None
    }, 200

# 静态文件服务 - 提供FILE_SAVE_DIR目录下的文件访问
import os
# 使用整个FILE_SAVE_DIR路径作为路由前缀（去除前导斜杠）
file_dir_prefix = config.FILE_SAVE_DIR.rstrip('/').lstrip('/')
# 创建动态路由
@app.route(f'/{file_dir_prefix}/<path:filename>')
def serve_file(filename):
    """提供静态文件访问服务，支持多级目录结构"""
    # 防止目录遍历攻击
    safe_filename = os.path.normpath(filename)
    if safe_filename.startswith('..') or os.path.isabs(safe_filename):
        logger.warning(f"尝试访问不安全的文件路径: {filename}")
        return {
            'code': 403,
            'msg': '禁止访问的文件路径',
            'data': None
        }, 200
    
    logger.info(f"访问文件: {safe_filename} 来自目录: {config.FILE_SAVE_DIR}")
    return send_from_directory(config.FILE_SAVE_DIR, safe_filename)

# 静态文件服务 - 提供前端打包文件访问
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dist_web')
if os.path.exists(static_dir):
    logger.info(f"Serving static files from: {static_dir}")
    # 设置静态文件目录
    app.static_folder = static_dir
    app.static_url_path = ''
    
    # 提供index.html作为默认首页
    @app.route('/')
    def serve_index():
        return send_from_directory(static_dir, 'index.html')
    
    # 处理单页应用的路由，所有未匹配的路由都返回index.html
    @app.route('/<path:path>')
    def serve_spa(path):
        # 如果文件存在则返回文件，否则返回index.html
        file_path = os.path.join(static_dir, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(static_dir, path)
        else:
            return send_from_directory(static_dir, 'index.html')
else:
    logger.warning(f"Static directory not found: {static_dir}")

# 404错误处理
@app.errorhandler(404)
def handle_404(e):
    """404错误处理"""
    logger.warning(f"404 Not Found: {request.path}")
    return {
        'code': 404,
        'msg': '接口不存在',
        'data': None
    }, 200

# 启动应用
if __name__ == '__main__':
    try:
        logger.info(f"启动API服务: {config.HOST}:{config.PORT} | DEBUG: {config.DEBUG}")
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG
        )
    except Exception as e:
        log_error(e, "FlaskApp", "Startup")
        logger.error("服务启动失败")
        print(traceback.format_exc())