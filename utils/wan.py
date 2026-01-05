import os
import sys
import random
from pathlib import Path
from argparse import Namespace

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import torch
import torch.distributed as dist
from loguru import logger

from LightX2V.lightx2v.common.ops import *
from LightX2V.lightx2v.models.runners.qwen_image.qwen_image_runner import QwenImageRunner  # noqa: F401
from LightX2V.lightx2v.models.runners.wan.wan_animate_runner import WanAnimateRunner  # noqa: F401
from LightX2V.lightx2v.models.runners.wan.wan_audio_runner import Wan22AudioRunner, WanAudioRunner  # noqa: F401
from LightX2V.lightx2v.models.runners.wan.wan_distill_runner import WanDistillRunner  # noqa: F401
# 手动注册 wan2.1_distill 以确保它在注册器中
from LightX2V.lightx2v.utils.registry_factory import RUNNER_REGISTER
import logging
logging.basicConfig(level=logging.INFO)

# 检查并手动注册
if 'wan2.1_distill' not in RUNNER_REGISTER:
    RUNNER_REGISTER.register(WanDistillRunner, key='wan2.1_distill')
    logging.info("手动注册 'wan2.1_distill' 到 RUNNER_REGISTER")

logging.info(f"WAN 模块导入后，RUNNER_REGISTER 中的键: {list(RUNNER_REGISTER.keys())}")
logging.info(f"'wan2.1_distill' 是否在注册器中: {'wan2.1_distill' in RUNNER_REGISTER}")
from LightX2V.lightx2v.models.runners.wan.wan_matrix_game2_runner import WanSFMtxg2Runner  # noqa: F401
from LightX2V.lightx2v.models.runners.wan.wan_runner import Wan22MoeRunner, WanRunner  # noqa: F401
from LightX2V.lightx2v.models.runners.wan.wan_sf_runner import WanSFRunner  # noqa: F401
from LightX2V.lightx2v.models.runners.wan.wan_vace_runner import WanVaceRunner  # noqa: F401
from LightX2V.lightx2v.models.runners.default_runner import DefaultRunner
from LightX2V.lightx2v.utils.envs import *
from LightX2V.lightx2v.utils.input_info import set_input_info
from LightX2V.lightx2v.utils.profiler import *
from LightX2V.lightx2v.utils.registry_factory import RUNNER_REGISTER
from LightX2V.lightx2v.utils.set_config import print_config, set_config, set_parallel_config
from LightX2V.lightx2v.utils.utils import seed_all
from LightX2V.lightx2v.utils.lockable_dict import LockableDict

class WanPipeRunner:
  def __init__(self, model_path: os.PathLike, config_json_path: os.PathLike, model_cls: str, task: str):
    self.model_cls = model_cls
    self.task = task
    self.model_path = str(Path(model_path).absolute())
    self.config_json = str(Path(config_json_path).absolute())
    self.use_prompt_enhancer = False
    self.negative_prompt = "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走"
    self.runner: DefaultRunner = None
    self.config: LockableDict = None

  def load(self):
    args = Namespace(
      model_cls=self.model_cls,
      task=self.task,
      model_path=self.model_path,
      config_json=self.config_json,
      use_prompt_enhancer=self.use_prompt_enhancer,
    )
    self.config: LockableDict = set_config(args)
    
    # 调试信息
    logging.info(f"set_config 返回的 config: {self.config}")
    logging.info(f"config 中的 model_cls: {self.config['model_cls']}")
    logging.info(f"RUNNER_REGISTER 中的键: {list(RUNNER_REGISTER.keys())}")
    
    if self.config["parallel"]:
      dist.init_process_group(backend="nccl")
      torch.cuda.set_device(dist.get_rank())
      set_parallel_config(self.config)
    print_config(self.config)

    torch.set_grad_enabled(False)
    # 确保使用的是正确的 model_cls
    model_cls = self.config["model_cls"]
    logging.info(f"正在从 RUNNER_REGISTER 中获取: {model_cls}")
    self.runner = RUNNER_REGISTER[model_cls](self.config)
    self.runner.init_modules()

  def infer(
    self,
    prompt: str,
    image_path: str | None = None,
    save_result_path: str = None,
    target_video_length: int | None = None,
    target_height: int | None = None,
    target_width: int | None = None,
    negative_prompt: str | None = None,
    seed: int | None = None,
    infer_steps: int | None = None,
  ):
    if seed is None:
      seed = random.randint(0, 2**32 - 1)
    if negative_prompt is None:
      negative_prompt = self.negative_prompt

    seed_all(seed)
    args = Namespace(
      model_cls=self.model_cls,
      task=self.task,
      model_path=self.model_path,
      config_json=self.config_json,
      use_prompt_enhancer=self.use_prompt_enhancer,
      prompt=prompt,
      negative_prompt=negative_prompt,
      image_path=image_path,
      save_result_path=save_result_path,
      seed=seed,
      return_result_tensor=False,
    )

    modify_config = target_video_length is not None or target_height is not None or target_width is not None
    saved_config = {
      "target_video_length": self.config["target_video_length"],
      "target_height": self.config["target_height"],
      "target_width": self.config["target_width"],
      "infer_steps": self.config["infer_steps"],
    }

    if modify_config:
      config_modify = {}
      if target_video_length is not None:
        if target_video_length % self.config["vae_stride"][0] != 1:
          logger.warning(f"`num_frames - 1` has to be divisible by {self.config['vae_stride'][0]}. Rounding to the nearest number.")
          target_video_length = target_video_length // self.config["vae_stride"][0] * self.config["vae_stride"][0] + 1
        config_modify["target_video_length"] = target_video_length
      if target_height is not None:
        config_modify["target_height"] = target_height
      if target_width is not None:
        config_modify["target_width"] = target_width
      if infer_steps is not None:
        config_modify["infer_steps"] = infer_steps

      self.runner.set_config(config_modify)

    with ProfilingContext4DebugL1("Total Cost"):
      input_info = set_input_info(args)
      self.runner.run_pipeline(input_info)

    if modify_config:
      self.runner.set_config(saved_config)


  def clean_up(self):
    # Clean up distributed process group
    if dist.is_initialized():
      dist.destroy_process_group()
      logger.info("Distributed process group cleaned up")