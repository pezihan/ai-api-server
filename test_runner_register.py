import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, '/Users/yinhua/Desktop/ai-api-server')

# 导入注册器
from LightX2V.lightx2v.utils.registry_factory import RUNNER_REGISTER

# 导入 WAN 相关模块
from LightX2V.lightx2v.models.runners.wan.wan_distill_runner import WanDistillRunner

# 打印注册器中的所有键
print(f"RUNNER_REGISTER 中的键: {list(RUNNER_REGISTER.keys())}")

# 检查 'wan2.1_distill' 是否在注册器中
if 'wan2.1_distill' in RUNNER_REGISTER:
    print("✓ 'wan2.1_distill' 已成功注册到 RUNNER_REGISTER")
else:
    print("✗ 'wan2.1_distill' 未注册到 RUNNER_REGISTER")
