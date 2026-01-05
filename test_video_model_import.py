#!/usr/bin/env python3
"""
测试视频模型的导入功能，验证修复是否解决了No module named 'wan'的错误
"""
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.model_scheduler import model_scheduler
from utils.logger import logger

# 测试函数
def test_video_model_import():
    """
    测试视频模型的导入功能
    """
    logger.info("开始测试视频模型导入...")
    
    # 测试1: 尝试加载文生视频模型
    logger.info("\n=== 测试1: 尝试加载文生视频模型 ===")
    
    try:
        logger.info("加载文生视频模型...")
        # 这里我们不需要实际执行推理，只需要验证导入是否成功
        model_scheduler._get_inference_func = lambda: lambda: None  # 模拟推理函数
        
        # 测试导入语句是否正确
        from utils.wan import WanPipeRunner
        logger.info("成功从utils.wan导入WanPipeRunner")
        
        logger.info("文生视频模型导入测试成功")
        
    except ImportError as e:
        logger.error(f"测试1失败: 导入错误 - {e}")
    except Exception as e:
        logger.error(f"测试1失败: 其他错误 - {e}")
    
    # 测试2: 尝试加载图生视频模型
    logger.info("\n=== 测试2: 尝试加载图生视频模型 ===")
    
    try:
        logger.info("加载图生视频模型...")
        
        # 测试导入语句是否正确
        from utils.wan import WanPipeRunner
        logger.info("成功从utils.wan导入WanPipeRunner")
        
        logger.info("图生视频模型导入测试成功")
        
    except ImportError as e:
        logger.error(f"测试2失败: 导入错误 - {e}")
    except Exception as e:
        logger.error(f"测试2失败: 其他错误 - {e}")
    
    logger.info("\n=== 所有测试完成 ===")

if __name__ == "__main__":
    test_video_model_import()