import os
import json
from config.config import config

# 任务类型映射
task_type_map = {
    'text2img': 'z_image',
    'img2img': 'qwen_image_edit',
    'text2video': 'wan_2_1_t2v',
    'img2video': 'wan_2_2_i2v'
}

# 加载lora配置文件
def load_lora_config():
    config_path = os.path.join(config.CONFIG_DIR, 'lora_config.json')
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 校验lora_id是否存在于配置文件中
def validate_lora_ids(task_type, lora_ids):
    lora_config = load_lora_config()
    config_key = task_type_map.get(task_type)
    if not config_key:
        return False, f'不支持的任务类型: {task_type}'
    
    lora_configs = lora_config.get(config_key, [])
    valid_lora_ids = [cfg.get('id') for cfg in lora_configs]
    
    for lora_id in lora_ids:
        if lora_id not in valid_lora_ids:
            return False, f'LoRA ID {lora_id} 不存在于配置文件中'
    
    return True, ''

# 校验lora文件是否存在
def validate_lora_files(task_type, lora_ids):
    lora_config = load_lora_config()
    config_key = task_type_map.get(task_type)
    if not config_key:
        return False, f'不支持的任务类型: {task_type}'
    
    lora_configs = lora_config.get(config_key, [])
    lora_dict = {cfg.get('id'): cfg.get('path') for cfg in lora_configs}
    
    for lora_id in lora_ids:
        lora_path = lora_dict.get(lora_id)
        if not lora_path:
            return False, f'LoRA ID {lora_id} 不存在于配置文件中'
        
        # 构建完整的lora文件路径
        full_lora_path = os.path.join(config.LORA_DIR, lora_path)
        if not os.path.exists(full_lora_path):
            return False, f'LoRA文件不存在: {full_lora_path}'
    
    return True, ''

# 获取任务类型对应的配置键
def get_config_key(task_type):
    return task_type_map.get(task_type)

# 根据任务类型和LoRA ID获取LoRA配置
def get_lora_configs(task_type, lora_ids):
    lora_config = load_lora_config()
    config_key = get_config_key(task_type)
    if not config_key:
        return []
    
    lora_configs = lora_config.get(config_key, [])
    result = []
    for cfg in lora_configs:
        if cfg.get('id') in lora_ids:
            # 复制配置并拼接完整路径
            config_copy = cfg.copy()
            if 'path' in config_copy:
                config_copy['path'] = os.path.join(config.LORA_DIR, config_copy['path'])
            result.append(config_copy)
    return result
