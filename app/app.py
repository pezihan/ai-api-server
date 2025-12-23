from flask import Flask, request
from flask_cors import CORS
from flask_restx import Api
from config.config import config
from utils.logger import logger, log_error
from middlewares.auth import auth_middleware
import traceback

# 导入API模块的命名空间
from app.api import auth_ns, health_ns, image_ns, video_ns, task_ns, upload_ns

# 创建Flask应用
app = Flask(__name__)

# 配置CORS
CORS(app)

# 创建API对象
api = Api(
    app,
    version='1.0',
    title='AI API Server',
    description='AI API服务接口文档',
    doc='/api/docs'  # 文档访问路径
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