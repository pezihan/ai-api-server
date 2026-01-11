#!/usr/bin/env python3
"""
任务工作器启动脚本
"""
import sys
import os
import signal

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger
from utils.task_worker import task_worker

def signal_handler(signum, frame):
    """信号处理函数"""
    logger.info(f"接收到信号: {signum}, 正在停止任务工作器...")
    task_worker.stop()
    sys.exit(0)

def main():
    """主函数"""
    try:
        # 注册信号处理
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("启动任务工作器...")
        task_worker.start()
        
    except KeyboardInterrupt:
        logger.info("任务工作器被用户中断")
    except Exception as e:
        logger.error(f"任务工作器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()