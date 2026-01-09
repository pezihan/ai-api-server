from flask import request
from flask_restx import Namespace, Resource, fields
from utils.logger import logger
from middlewares.auth import auth_required
import os
import json
from config.config import config

# 创建命名空间
lora_ns = Namespace('lora', description='LoRA配置接口')

@lora_ns.route('/config')
class LoraConfig(Resource):
    @lora_ns.response(200, '获取LoRA配置成功')
    @auth_required
    def get(self):
        """
        获取LoRA配置
        返回lora_config.json的内容，按任务类型组织的LoRA模型配置
        """
        try:
            config_path = os.path.join(config.CONFIG_DIR, 'lora_config.json')
            if not os.path.exists(config_path):
                logger.warning(f"LoRA配置文件不存在: {config_path}")
                return {'code': 404, 'msg': 'LoRA配置文件不存在', 'data': None}, 200
            
            # 加载并返回配置文件内容
            with open(config_path, 'r', encoding='utf-8') as f:
                lora_config = json.load(f)
            
            return {
                'code': 200,
                'msg': '获取LoRA配置成功',
                'data': lora_config
            }, 200
            
        except Exception as e:
            logger.error(f"获取LoRA配置失败: {e}")
            return {'code': 500, 'msg': '获取LoRA配置失败', 'data': None}, 200
