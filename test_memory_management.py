#!/usr/bin/env python3
"""
测试内存管理功能的脚本
"""
import sys
import os
import time
import gc
import torch

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.model_scheduler import model_scheduler
from utils.logger import logger

def test_memory_management():
    """测试内存管理功能"""
    print("=== 开始测试内存管理功能 ===")
    
    # 测试前的内存状态
    if torch.cuda.is_available():
        before_memory = model_scheduler.get_gpu_memory_info()
        print(f"测试前GPU内存: {before_memory}")
    
    # 测试1: 加载和卸载模型
    print("\n测试1: 加载和卸载text2img模型")
    try:
        # 这里使用不存在的模型路径来模拟加载失败的情况
        pipe = model_scheduler.load_model(
            task_type='text2img',
            model_path='invalid_model_path'
        )
    except Exception as e:
        print(f"加载模型失败 (预期行为): {e}")
    
    # 检查内存释放情况
    if torch.cuda.is_available():
        after_memory = model_scheduler.get_gpu_memory_info()
        print(f"测试后GPU内存: {after_memory}")
        
        # 计算内存变化
        if 'reserved' in before_memory and 'reserved' in after_memory:
            memory_diff = after_memory['reserved'] - before_memory['reserved']
            print(f"GPU内存变化: {memory_diff:.2f} GB")
            if memory_diff < 0.1:  # 允许微小波动
                print("✅ 内存释放成功!")
            else:
                print("❌ 内存没有完全释放!")
    
    # 测试2: 模拟任务执行失败后的内存释放
    print("\n测试2: 模拟任务执行过程中的异常")
    
    # 定义一个模拟任务执行的函数
    def simulate_task_execution():
        try:
            # 模拟加载模型
            pipe = model_scheduler.load_model(task_type='text2img')
            
            # 模拟任务执行过程中的异常
            raise RuntimeError("模拟任务执行异常")
            
        except Exception as e:
            print(f"任务执行异常 (预期行为): {e}")
            # 模拟task_worker中的finally块
            model_scheduler.unload_model()
    
    simulate_task_execution()
    
    # 检查内存释放情况
    if torch.cuda.is_available():
        after_memory = model_scheduler.get_gpu_memory_info()
        print(f"异常后GPU内存: {after_memory}")
        
        if 'reserved' in before_memory and 'reserved' in after_memory:
            memory_diff = after_memory['reserved'] - before_memory['reserved']
            print(f"异常后GPU内存变化: {memory_diff:.2f} GB")
            if memory_diff < 0.1:  # 允许微小波动
                print("✅ 异常后内存释放成功!")
            else:
                print("❌ 异常后内存没有完全释放!")
    
    # 测试3: 测试多次任务执行
    print("\n测试3: 测试多次任务执行")
    
    for i in range(3):
        print(f"\n执行第 {i+1} 次任务")
        try:
            # 模拟加载模型
            pipe = model_scheduler.load_model(task_type='text2img')
            
            # 模拟任务执行
            time.sleep(0.5)
            
            # 模拟任务完成
            model_scheduler.unload_model()
            
            if torch.cuda.is_available():
                current_memory = model_scheduler.get_gpu_memory_info()
                print(f"任务 {i+1} 完成后GPU内存: {current_memory}")
                
        except Exception as e:
            print(f"任务 {i+1} 执行失败: {e}")
            model_scheduler.unload_model()
    
    # 最终内存状态
    if torch.cuda.is_available():
        final_memory = model_scheduler.get_gpu_memory_info()
        print(f"\n最终GPU内存: {final_memory}")
        
        if 'reserved' in before_memory and 'reserved' in final_memory:
            memory_diff = final_memory['reserved'] - before_memory['reserved']
            print(f"总内存变化: {memory_diff:.2f} GB")
            if memory_diff < 0.1:  # 允许微小波动
                print("✅ 多次任务后内存释放成功!")
            else:
                print("❌ 多次任务后内存有泄漏!")
    
    print("\n=== 内存管理测试完成 ===")

if __name__ == "__main__":
    test_memory_management()
