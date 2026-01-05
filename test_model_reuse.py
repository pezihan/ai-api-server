import os
import sys
import time
from utils.model_scheduler import model_scheduler
from utils.logger import logger

# 设置环境变量以便正确导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_model_reuse():
    """测试模型复用功能"""
    logger.info("开始测试模型复用功能")
    
    try:
        # 第一次加载图片模型
        logger.info("第一次加载text2img模型")
        start_time = time.time()
        pipe1 = model_scheduler.load_model(task_type='text2img')
        load_time1 = time.time() - start_time
        logger.info(f"第一次加载耗时: {load_time1:.2f} 秒")
        
        # 第二次加载相同类型的模型，应该复用
        logger.info("\n第二次加载text2img模型（应该复用）")
        start_time = time.time()
        pipe2 = model_scheduler.load_model(task_type='text2img')
        load_time2 = time.time() - start_time
        logger.info(f"第二次加载耗时: {load_time2:.2f} 秒")
        
        # 验证是否是同一个模型实例
        if pipe1 is pipe2:
            logger.info("✓ 模型实例复用成功")
        else:
            logger.warning("⚠ 模型实例未复用")
        
        # 验证加载时间（复用应该更快）
        if load_time2 < load_time1 * 0.1:  # 复用应该比首次加载快10倍以上
            logger.info("✓ 复用加载时间正常（比首次加载快10倍以上）")
        else:
            logger.warning(f"⚠ 复用加载时间异常: 首次加载{load_time1:.2f}秒, 复用加载{load_time2:.2f}秒")
        
        # 加载不同类型的模型，应该先卸载再加载
        logger.info("\n加载img2img模型（不同任务类型）")
        start_time = time.time()
        pipe3 = model_scheduler.load_model(task_type='img2img')
        load_time3 = time.time() - start_time
        logger.info(f"加载img2img模型耗时: {load_time3:.2f} 秒")
        
        # 验证是否是新模型实例
        if pipe3 is not pipe1:
            logger.info("✓ 不同任务类型加载了新模型实例")
        else:
            logger.warning("⚠ 不同任务类型未加载新模型")
        
        # 再次加载text2img模型，应该重新加载
        logger.info("\n再次加载text2img模型")
        start_time = time.time()
        pipe4 = model_scheduler.load_model(task_type='text2img')
        load_time4 = time.time() - start_time
        logger.info(f"再次加载text2img模型耗时: {load_time4:.2f} 秒")
        
        # 清理测试
        model_scheduler.unload_model()
        logger.info("\n✓ 模型复用测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 确保模型已卸载
        model_scheduler.unload_model()
    
    return True

if __name__ == "__main__":
    test_model_reuse()