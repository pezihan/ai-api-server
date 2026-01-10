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

# 加载lora配置（从目录读取）
def load_lora_config():
    # 定义需要读取的LoRA目录
    lora_dirs = ['wan_2_1_t2v', 'wan_2_2_i2v', 'qwen_image_edit', 'z_image']
    lora_config = {}
    
    for lora_dir in lora_dirs:
        dir_path = os.path.join(config.LORA_DIR, lora_dir)
        # 如果目录不存在，创建一个目录
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            lora_config[lora_dir] = []
            continue
        
        lora_items = []
        # 遍历目录下的文件和子目录
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            
            # 对于wan_2_2_i2v目录，需要特殊处理
            if lora_dir == 'wan_2_2_i2v':
                if os.path.isdir(item_path):
                    # 检查子目录下是否有high_noise_model.safetensors或low_noise_model.safetensors
                    high_noise_path = os.path.join(item_path, 'high_noise_model.safetensors')
                    low_noise_path = os.path.join(item_path, 'low_noise_model.safetensors')
                    
                    lora_item = {'name': item}
                    if os.path.exists(high_noise_path):
                        lora_item['high_noise_model'] = {
                            'path': os.path.join(lora_dir, item, 'high_noise_model.safetensors')
                        }
                    if os.path.exists(low_noise_path):
                        lora_item['low_noise_model'] = {
                            'path': os.path.join(lora_dir, item, 'low_noise_model.safetensors')
                        }
                    if 'high_noise_model' in lora_item or 'low_noise_model' in lora_item:
                        lora_items.append(lora_item)
            else:
                # 对于其他目录，直接处理.safetensors文件
                if os.path.isfile(item_path) and item.endswith('.safetensors'):
                    # 从文件名中提取模型名（去掉.safetensors后缀）
                    model_name = item[:-len('.safetensors')]
                    lora_item = {
                        'name': model_name,
                        'path': os.path.join(lora_dir, item)
                    }
                    lora_items.append(lora_item)
        
        lora_config[lora_dir] = lora_items
    
    return lora_config

# 校验lora_names是否存在
def validate_lora_names(task_type, lora_names):
    lora_config = load_lora_config()
    config_key = task_type_map.get(task_type)
    if not config_key:
        return False, f'不支持的任务类型: {task_type}'
    
    lora_configs = lora_config.get(config_key, [])
    valid_lora_names = [cfg.get('name') for cfg in lora_configs]
    
    for lora_name in lora_names:
        if lora_name not in valid_lora_names:
            return False, f'LoRA模型名 {lora_name} 不存在'
    
    return True, ''

# 校验lora文件是否存在
def validate_lora_files(task_type, lora_names):
    lora_config = load_lora_config()
    config_key = task_type_map.get(task_type)
    if not config_key:
        return False, f'不支持的任务类型: {task_type}'
    
    lora_configs = lora_config.get(config_key, [])
    lora_dict = {cfg.get('name'): cfg for cfg in lora_configs}
    
    for lora_name in lora_names:
        lora_cfg = lora_dict.get(lora_name)
        if not lora_cfg:
            return False, f'LoRA模型名 {lora_name} 不存在'
        
        # 检查直接的path字段
        if 'path' in lora_cfg:
            lora_path = lora_cfg.get('path')
            if lora_path:
                full_lora_path = os.path.join(config.LORA_DIR, lora_path)
                if not os.path.exists(full_lora_path):
                    return False, f'LoRA文件不存在: {full_lora_path}'
        
        # 检查high_noise_model字段
        if 'high_noise_model' in lora_cfg:
            high_noise_path = lora_cfg['high_noise_model'].get('path')
            if high_noise_path:
                full_high_noise_path = os.path.join(config.LORA_DIR, high_noise_path)
                if not os.path.exists(full_high_noise_path):
                    return False, f'LoRA高噪声模型文件不存在: {full_high_noise_path}'
        
        # 检查low_noise_model字段
        if 'low_noise_model' in lora_cfg:
            low_noise_path = lora_cfg['low_noise_model'].get('path')
            if low_noise_path:
                full_low_noise_path = os.path.join(config.LORA_DIR, low_noise_path)
                if not os.path.exists(full_low_noise_path):
                    return False, f'LoRA低噪声模型文件不存在: {full_low_noise_path}'
    
    return True, ''

# 获取任务类型对应的配置键
def get_config_key(task_type):
    return task_type_map.get(task_type)

# 根据任务类型和LoRA名称获取LoRA配置
def get_lora_configs(task_type, lora_names):
    lora_config = load_lora_config()
    config_key = get_config_key(task_type)
    if not config_key:
        return []
    
    lora_configs = lora_config.get(config_key, [])
    result = []
    for cfg in lora_configs:
        if cfg.get('name') in lora_names:
            # 复制配置并拼接完整路径
            config_copy = cfg.copy()
            if 'path' in config_copy:
                config_copy['path'] = os.path.join(config.LORA_DIR, config_copy['path'])
            
            # 处理high_noise_model字段
            if 'high_noise_model' in config_copy and 'path' in config_copy['high_noise_model']:
                config_copy['high_noise_model']['path'] = os.path.join(config.LORA_DIR, config_copy['high_noise_model']['path'])
            
            # 处理low_noise_model字段
            if 'low_noise_model' in config_copy and 'path' in config_copy['low_noise_model']:
                config_copy['low_noise_model']['path'] = os.path.join(config.LORA_DIR, config_copy['low_noise_model']['path'])
            
            result.append(config_copy)
    return result
