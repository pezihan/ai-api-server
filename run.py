#!/usr/bin/env python3
"""服务启动入口文件"""

from app.app import app
from utils.logger import logger

if __name__ == '__main__':
    try:
        logger.info("从run.py启动API服务")
        app.run()
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        import traceback
        traceback.print_exc()