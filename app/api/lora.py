from flask_restx import Namespace, Resource
from utils.logger import logger
from middlewares.auth import auth_required
from utils.lora_utils import load_lora_config

# 创建命名空间
lora_ns = Namespace('lora', description='LoRA配置接口')

@lora_ns.route('/config')
class LoraConfig(Resource):
    @lora_ns.response(200, '获取LoRA配置成功')
    @auth_required
    def get(self):
        """
        获取LoRA配置
        从LORA_DIR目录读取配置，按任务类型组织的LoRA模型配置
        """
        try:
            # 直接调用lora_utils.py中的函数获取配置
            lora_config = load_lora_config()
            
            return {
                'code': 200,
                'msg': '获取LoRA配置成功',
                'data': lora_config
            }, 200
            
        except Exception as e:
            logger.error(f"获取LoRA配置失败: {e}")
            return {'code': 500, 'msg': '获取LoRA配置失败', 'data': None}, 200
