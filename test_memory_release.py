import os
import sys
import time
import psutil
from utils.model_scheduler import model_scheduler
from utils.logger import logger

# 设置环境变量以便正确导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_process_memory_usage():
    """获取当前进程的内存使用情况"""
    process = psutil.Process()
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)  # 返回GB

def get_gpu_memory_info():
    """获取GPU内存使用情况"""
    if model_scheduler.get_gpu_memory_info():
        return model_scheduler.get_gpu_memory_info()
    return None

def test_model_unload_memory_release():
    """测试模型卸载时的内存释放情况"""
    logger.info("开始测试模型卸载内存释放")
    
    # 记录初始内存使用
    initial_cpu_mem = get_process_memory_usage()
    initial_gpu_mem = get_gpu_memory_info()
    logger.info(f"初始CPU内存使用: {initial_cpu_mem:.2f} GB")
    if initial_gpu_mem:
        logger.info(f"初始GPU内存使用: {initial_gpu_mem}")
    
    try:
        # 加载图片模型
        logger.info("加载图片生成模型")
        model_scheduler.load_model(task_type='text2img')
        
        # 记录加载后的内存使用
        after_load_cpu_mem = get_process_memory_usage()
        after_load_gpu_mem = get_gpu_memory_info()
        logger.info(f"模型加载后CPU内存使用: {after_load_cpu_mem:.2f} GB")
        if after_load_gpu_mem:
            logger.info(f"模型加载后GPU内存使用: {after_load_gpu_mem}")
        
        cpu_mem_increase = after_load_cpu_mem - initial_cpu_mem
        logger.info(f"CPU内存增加: {cpu_mem_increase:.2f} GB")
        
        # 等待几秒钟
        time.sleep(3)
        
        # 卸载模型
        logger.info("卸载模型")
        model_scheduler.unload_model()
        
        # 等待几秒钟让内存释放完成
        time.sleep(5)
        
        # 记录卸载后的内存使用
        after_unload_cpu_mem = get_process_memory_usage()
        after_unload_gpu_mem = get_gpu_memory_info()
        logger.info(f"模型卸载后CPU内存使用: {after_unload_cpu_mem:.2f} GB")
        if after_unload_gpu_mem:
            logger.info(f"模型卸载后GPU内存使用: {after_unload_gpu_mem}")
        
        cpu_mem_decrease = after_load_cpu_mem - after_unload_cpu_mem
        cpu_mem_diff = after_unload_cpu_mem - initial_cpu_mem
        logger.info(f"CPU内存释放: {cpu_mem_decrease:.2f} GB")
        logger.info(f"最终CPU内存差异（与初始相比）: {cpu_mem_diff:.2f} GB")
        
        # 验证内存释放效果
        if cpu_mem_diff < cpu_mem_increase * 0.1:  # 允许10%的残留
            logger.info("✓ CPU内存释放效果良好")
        else:
            logger.warning(f"⚠ CPU内存释放不彻底，仍有 {cpu_mem_diff:.2f} GB 残留")
            
        # 测试视频模型
        logger.info("\n加载视频生成模型")
        model_scheduler.load_model(task_type='text2video')
        
        # 记录加载后的内存使用
        after_video_load_cpu_mem = get_process_memory_usage()
        after_video_load_gpu_mem = get_gpu_memory_info()
        logger.info(f"视频模型加载后CPU内存使用: {after_video_load_cpu_mem:.2f} GB")
        if after_video_load_gpu_mem:
            logger.info(f"视频模型加载后GPU内存使用: {after_video_load_gpu_mem}")
        
        # 卸载模型
        logger.info("卸载视频模型")
        model_scheduler.unload_model()
        
        # 记录卸载后的内存使用
        after_video_unload_cpu_mem = get_process_memory_usage()
        after_video_unload_gpu_mem = get_gpu_memory_info()
        logger.info(f"视频模型卸载后CPU内存使用: {after_video_unload_cpu_mem:.2f} GB")
        if after_video_unload_gpu_mem:
            logger.info(f"视频模型卸载后GPU内存使用: {after_video_unload_gpu_mem}")
        
        video_cpu_mem_diff = after_video_unload_cpu_mem - initial_cpu_mem
        logger.info(f"最终CPU内存差异（与初始相比）: {video_cpu_mem_diff:.2f} GB")
        
        if video_cpu_mem_diff < 0.5:  # 允许0.5GB的残留
            logger.info("✓ 视频模型CPU内存释放效果良好")
        else:
            logger.warning(f"⚠ 视频模型CPU内存释放不彻底，仍有 {video_cpu_mem_diff:.2f} GB 残留")
            
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保模型已卸载
        model_scheduler.unload_model()
        logger.info("测试完成")

if __name__ == "__main__":
    test_model_unload_memory_release()