#!/usr/bin/env python3
"""
测试模型调度器的内存管理功能
"""
import sys
import os
import time
import torch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.model_scheduler import model_scheduler
from utils.logger import logger

# 测试函数
def test_model_scheduler():
    """
    测试模型调度器的内存管理功能
    """
    logger.info("开始测试模型调度器...")
    
    # 测试1: 加载和卸载文生图模型
    logger.info("\n=== 测试1: 加载和卸载文生图模型 ===")
    
    try:
        # 加载模型
        logger.info("加载文生图模型...")
        t2i_pipe = model_scheduler.load_model(task_type='text2img')
        logger.info("文生图模型加载成功")
        
        # 模拟推理
        logger.info("模拟文生图推理...")
        result = t2i_pipe(
            prompt="A beautiful landscape",
            negative_prompt="ugly",
            width=512,
            height=512,
            num_inference_steps=1,
            guidance_scale=5.0
        )
        logger.info("文生图推理完成")
        
        # 卸载模型
        logger.info("卸载文生图模型...")
        model_scheduler.unload_model()
        logger.info("文生图模型卸载完成")
        
    except Exception as e:
        logger.error(f"测试1失败: {e}")
    
    # 等待内存释放
    time.sleep(2)
    
    # 测试2: 加载和卸载图生图模型
    logger.info("\n=== 测试2: 加载和卸载图生图模型 ===")
    
    try:
        # 加载模型
        logger.info("加载图生图模型...")
        i2i_pipe = model_scheduler.load_model(task_type='img2img')
        logger.info("图生图模型加载成功")
        
        # 卸载模型
        logger.info("卸载图生图模型...")
        model_scheduler.unload_model()
        logger.info("图生图模型卸载完成")
        
    except Exception as e:
        logger.error(f"测试2失败: {e}")
    
    # 等待内存释放
    time.sleep(2)
    
    # 测试3: 模型复用
    logger.info("\n=== 测试3: 模型复用功能 ===")
    
    try:
        # 第一次加载模型
        logger.info("第一次加载文生图模型...")
        t2i_pipe1 = model_scheduler.load_model(task_type='text2img')
        logger.info("文生图模型加载成功 (第一次)")
        
        # 第二次加载相同任务类型的模型（应该复用）
        logger.info("第二次加载文生图模型 (应该复用)...")
        t2i_pipe2 = model_scheduler.load_model(task_type='text2img')
        logger.info("文生图模型加载成功 (第二次)")
        
        # 卸载模型
        logger.info("卸载文生图模型...")
        model_scheduler.unload_model()
        logger.info("文生图模型卸载完成")
        
    except Exception as e:
        logger.error(f"测试3失败: {e}")
    
    # 等待内存释放
    time.sleep(2)
    
    logger.info("\n=== 所有测试完成 ===")

if __name__ == "__main__":
    test_model_scheduler()