import os
import random
from pathlib import Path
from argparse import Namespace
import logging
from typing import Optional, TypedDict
from config.config import config
logging.basicConfig(level=logging.INFO)
import sys

# 添加 LightX2V 目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lightx2v_root = os.path.join(project_root, 'LightX2V')
sys.path.insert(0, lightx2v_root)
logging.info(f"Added LightX2V root to path: {lightx2v_root}")

import torch
import torch.distributed as dist
from loguru import logger

from lightx2v.common.ops import *
from lightx2v.utils.registry_factory import RUNNER_REGISTER
from lightx2v.models.runners.qwen_image.qwen_image_runner import QwenImageRunner  # noqa: F401
from lightx2v.models.runners.wan.wan_animate_runner import WanAnimateRunner  # noqa: F401
from lightx2v.models.runners.wan.wan_audio_runner import Wan22AudioRunner, WanAudioRunner  # noqa: F401
from lightx2v.models.runners.wan.wan_distill_runner import WanDistillRunner  # noqa: F401
from lightx2v.models.runners.wan.wan_matrix_game2_runner import WanSFMtxg2Runner  # noqa: F401
from lightx2v.models.runners.wan.wan_runner import Wan22MoeRunner, WanRunner  # noqa: F401
from lightx2v.models.runners.wan.wan_sf_runner import WanSFRunner  # noqa: F401
from lightx2v.models.runners.wan.wan_vace_runner import WanVaceRunner  # noqa: F401
from lightx2v.models.runners.default_runner import DefaultRunner
from lightx2v.utils.envs import *
from lightx2v.utils.input_info import set_input_info
from lightx2v.utils.profiler import *
from lightx2v.utils.set_config import print_config, set_config, set_parallel_config
from lightx2v.utils.utils import seed_all
from lightx2v.utils.lockable_dict import LockableDict

class LoraConfig(TypedDict):
    name: str | None
    path: str
    strength: Optional[float]
    
class WanModelPipeRunner:
  def __init__(self, model_path: os.PathLike, config_json_path: os.PathLike, model_cls: str, task: str, lora_configs: Optional[list[LoraConfig]] = None):
    self.model_cls = model_cls
    self.task = task
    self.model_path = str(Path(model_path).absolute())
    self.config_json = str(Path(config_json_path).absolute())
    self.use_prompt_enhancer = False
    self.negative_prompt = "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走"
    self.runner: DefaultRunner = None
    self.config: LockableDict = None
    self.lora_configs: Optional[list[LoraConfig]] = lora_configs

  def load(self):
    video_frame_interpolation = None
    # 判断是否要开启视频插帧
    if config.get('RIFE_STATE', False):
      video_frame_interpolation = {
        "algo": "rife",
        "target_fps": 32,
        "model_path": os.path.join(config.MODEL_DIR, "rife_model")
      }
    args = Namespace(
      model_cls=self.model_cls,
      task=self.task,
      model_path=self.model_path,
      config_json=self.config_json,
      use_prompt_enhancer=self.use_prompt_enhancer,
      lora_configs=self.lora_configs,
      video_frame_interpolation=video_frame_interpolation
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
    self.runner = RUNNER_REGISTER[self.config["model_cls"]](self.config)
    self.runner.init_modules()
    

  def infer(
    self, 
    prompt: str,
    image_path: str | None = None, 
    save_result_path: str | None = None, 
    target_video_length: int | None = None,
    target_height: int | None = None,
    target_width: int | None = None,
    negative_prompt: str | None = None, 
    seed: int | None = None,
    infer_steps: int | None = None
  ):
     # 检查self.runner是否为None
    if self.runner is None:
        logging.error("self.runner 为 None，无法执行推理")
        raise RuntimeError("self.runner 为 None，无法执行推理。请先正确加载模型。")
    
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
    config_modify = {}
    if modify_config:
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

  
  def clean_up(self):
    # Clean up distributed process group
    if dist.is_initialized():
      dist.destroy_process_group()
      logger.info("Distributed process group cleaned up")