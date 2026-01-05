import sys
import os
import time
from utils.model_scheduler import model_scheduler
from utils.logger import logger

# 设置日志级别
import logging
logging.basicConfig(level=logging.INFO)

def test_memory_release():
    """
    测试模型卸载时的内存释放情况
    """
    try:
        logger.info("=== 开始测试模型内存释放 ===")
        
        # 1. 加载text2img模型
        logger.info("1. 加载text2img模型...")
        pipe = model_scheduler.load_model('text2img')
        time.sleep(2)  # 等待模型完全加载
        
        # 2. 记录内存使用情况
        from utils.model_scheduler import model_scheduler as ms
        gpu_memory_after_load = ms.get_gpu_memory_info()
        cpu_memory_after_load = ms.get_cpu_memory_usage()
        logger.info(f"模型加载后GPU内存使用: {gpu_memory_after_load}")
        logger.info(f"模型加载后CPU内存使用: {cpu_memory_after_load}")
        
        # 3. 卸载模型
        logger.info("\n2. 卸载模型...")
        ms.unload_model()
        
        # 4. 再次记录内存使用情况
        time.sleep(2)  # 等待内存完全释放
        gpu_memory_after_unload = ms.get_gpu_memory_info()
        cpu_memory_after_unload = ms.get_cpu_memory_usage()
        logger.info(f"模型卸载后GPU内存使用: {gpu_memory_after_unload}")
        logger.info(f"模型卸载后CPU内存使用: {cpu_memory_after_unload}")
        
        # 5. 计算内存释放量
        if gpu_memory_after_load and gpu_memory_after_unload:
            gpu_freed = gpu_memory_after_load.get('reserved', 0) - gpu_memory_after_unload.get('reserved', 0)
            logger.info(f"GPU内存释放量: {gpu_freed:.2f} GB")
        
        if cpu_memory_after_load and cpu_memory_after_unload:
            cpu_freed = cpu_memory_after_load.get('process_used', 0) - cpu_memory_after_unload.get('process_used', 0)
            logger.info(f"CPU内存释放量: {cpu_freed:.2f} GB")
            
            if cpu_freed > 0:
                logger.info("✅ CPU内存释放成功!")
            else:
                logger.warning("❌ CPU内存没有有效释放!")
        
        logger.info("\n=== 测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_memory_release()
