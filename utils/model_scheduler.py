import os
import gc
import traceback
import multiprocessing as mp
import time
from typing import Optional, TypedDict, List
from utils.logger import logger
from config.config import config

# Set PyTorch CUDA memory allocation configuration to avoid fragmentation
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')


class ModelLoraConfig(TypedDict):
    name: str | None
    path: str
    strength: Optional[float | int] | None

class LoraConfig(TypedDict):
    id: int
    name: str
    high_noise_model: ModelLoraConfig
    low_noise_model: ModelLoraConfig
    path: str | None
    strength: Optional[float] | None

# 格式化模型的LoRA配置
def _format_lora_configs(lora_configs: Optional[List[LoraConfig]] | None) -> Optional[List[ModelLoraConfig]] | None:
    """
    格式化Wan模型的LoRA配置列表，处理high_noise_model和low_noise_model字段
    
    Args:
        lora_configs: 原始LoRA配置列表
        
    Returns:
        格式化后的LoRA配置列表，包含处理后的噪声模型配置
    """
    if not lora_configs:
        return None
    
    formatted_configs = []
    for cfg in lora_configs:
        # 处理high_noise_model字段
        if 'high_noise_model' in cfg:
            high_noise_config = {
                'name': 'high_noise_model',
                'path': cfg['high_noise_model'].get('path'),
                'strength': cfg['high_noise_model'].get('strength')
            }
            formatted_configs.append(high_noise_config)
        
        # 处理low_noise_model字段
        if 'low_noise_model' in cfg:
            low_noise_config = {
                'name': 'low_noise_model',
                'path': cfg['low_noise_model'].get('path'),
                'strength': cfg['low_noise_model'].get('strength')
            }
            formatted_configs.append(low_noise_config)
        
        # 保持对原始path字段的兼容支持
        if 'path' in cfg and cfg.get('path'):
            original_config = {
                'name': cfg.get('name'),
                'path': cfg.get('path'),
                'strength': cfg.get('strength')
            }
            formatted_configs.append(original_config)
    
    return formatted_configs

# 定义进程间通信的消息类型
class ModelMessage:
    """模型进程间通信消息"""
    def __init__(self, msg_type, task_type=None, params=None, result=None, error=None):
        self.msg_type = msg_type  # 'load', 'run', 'unload', 'exit', 'result', 'error'
        self.task_type = task_type
        self.params = params
        self.result = result
        self.error = error

# 模型工作进程函数
def model_worker_process(task_queue, result_queue):
    """模型工作进程，负责加载和运行模型"""
    import torch
    from utils.logger import logger
    
    # 重定向日志
    logger.info("模型工作进程启动")
    
    current_task = None
    model_pipeline = None
    
    try:
        while True:
            # 获取任务消息
            try:
                msg = task_queue.get()
            except Exception as e:
                logger.error(f"获取任务消息失败: {e}")
                time.sleep(0.1)
                continue
            
            if msg.msg_type == 'exit':
                logger.info("收到退出消息，模型工作进程将退出")
                break
            
            elif msg.msg_type == 'load':
                # 加载模型
                try:
                    logger.info(f"模型工作进程加载模型: {msg.task_type}")
                    # 从params中获取lora_configs
                    lora_configs = msg.params.get('lora_configs')
                    logger.info(f"lora配置: {lora_configs}")
                    # 根据任务类型加载不同模型
                    if msg.task_type == 'text2img':
                        model_pipeline = _load_zimage_t2i_model_worker(msg.params)
                    elif msg.task_type == 'img2img':
                        model_pipeline = _load_qwen_i2i_model_worker(msg.params)
                    elif msg.task_type == 'text2video':
                        model_pipeline = _load_wan_t2v_model_worker(msg.params, lora_configs=lora_configs)
                    elif msg.task_type == 'img2video':
                        model_pipeline = _load_wan_i2v_model_worker(msg.params, lora_configs=lora_configs)
                    
                    current_task = msg.task_type
                    logger.info(f"模型 (任务: {current_task}) 加载成功")
                    result_queue.put(ModelMessage('result', msg.task_type, result="success"))
                except Exception as e:
                    import traceback
                    error_traceback = traceback.format_exc()
                    logger.error(f"模型工作进程加载模型失败: {e}\n{error_traceback}")
                    result_queue.put(ModelMessage('error', msg.task_type, error=f"模型工作进程加载模型失败: {e}\n{error_traceback}"))
                    # 清理模型引用
                    if model_pipeline is not None:
                        try:
                            del model_pipeline
                            model_pipeline = None
                        except:
                            pass
                    current_task = None
            
            elif msg.msg_type == 'run':
                # 运行模型
                try:
                    logger.info(f"模型工作进程运行任务: {msg.task_type}")
                    if model_pipeline is None:
                        raise RuntimeError("模型未加载")
                    lora_configs = msg.params.get('lora_configs')
                    if 'lora_configs' in msg.params:
                        del msg.params['lora_configs']
                    formatted_lora_configs = _format_lora_configs(lora_configs)
                    logger.info(f"导入模型lora配置: {formatted_lora_configs}")
                    # 执行推理
                    if hasattr(model_pipeline, 'infer'):
                        result = model_pipeline.infer(**msg.params)
                    else:
                        # 卸载历史LoRA
                        if hasattr(model_pipeline, 'unload_lora_weights'):
                            try:
                                model_pipeline.unload_lora_weights()
                                logger.info("已卸载历史LoRA")
                            except Exception as e:
                                logger.error(f"卸载LoRA失败: {e}")
                        # 动态加载/切换LoRA
                        if hasattr(model_pipeline, 'load_lora_weights'):
                            if formatted_lora_configs is not None:
                                for lora_cfg in formatted_lora_configs:
                                    lora_path = lora_cfg.get('path')
                                    strength = lora_cfg.get('strength', 1.0)
                                    if lora_path:
                                        try:
                                            model_pipeline.load_lora_weights(lora_path, scale=strength)
                                            logger.info(f"成功加载LoRA: {lora_cfg.get('name')} (强度: {strength})")
                                        except Exception as e:
                                            logger.error(f"加载LoRA失败: {e}")

                        result = model_pipeline(**msg.params)
                    logger.info(f"模型工作进程任务完成: {msg.task_type}")
                    result_queue.put(ModelMessage('result', msg.task_type, result=result))
                except Exception as e:
                    import traceback
                    error_traceback = traceback.format_exc()
                    logger.error(f"模型工作进程运行任务失败: {e}\n{error_traceback}")
                    result_queue.put(ModelMessage('error', msg.task_type, error=f"模型工作进程运行任务失败: {e}\n{error_traceback}"))
            
            elif msg.msg_type == 'unload':
                # 卸载模型
                try:
                    logger.info(f"模型工作进程卸载模型: {current_task}")
                    if model_pipeline is not None:
                        if hasattr(model_pipeline, 'cleanup'):
                            try:
                                model_pipeline.cleanup()
                            except Exception as cleanup_error:
                                logger.warning(f"模型清理失败: {cleanup_error}")
                        del model_pipeline
                        model_pipeline = None
                    current_task = None
                    
                    # 清理GPU显存（仅在CUDA上下文有效的情况下）
                    try:
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                            torch.cuda.ipc_collect()
                            torch.cuda.synchronize()
                    except (torch.cuda.CudaError, torch.AcceleratorError) as e:
                        logger.warning(f"清理CUDA显存时出错: {e}")
                    
                    # 清理内存
                    gc.collect()
                    logger.info("模型工作进程模型卸载完成")
                    result_queue.put(ModelMessage('result', msg.task_type, result="success"))
                except Exception as e:
                    import traceback
                    error_traceback = traceback.format_exc()
                    logger.error(f"模型工作进程卸载模型失败: {e}\n{error_traceback}")
                    result_queue.put(ModelMessage('error', msg.task_type, error=f"模型工作进程卸载模型失败: {e}\n{error_traceback}"))
    
    except Exception as e:
        # 捕获并记录详细的异常信息，包括堆栈
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"模型工作进程异常退出: {e}\n{error_traceback}")
        # 尝试发送错误消息，包含详细的堆栈信息
        try:
            result_queue.put(ModelMessage('error', None, error=f"模型工作进程异常退出: {e}\n{error_traceback}"))
        except:
            pass
    finally:
        # 清理资源
        if model_pipeline is not None:
            try:
                if hasattr(model_pipeline, 'cleanup'):
                    model_pipeline.cleanup()
                del model_pipeline
            except:
                pass
        
        # 清理GPU显存（仅在CUDA上下文有效的情况下）
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
                torch.cuda.synchronize()
        except (torch.cuda.CudaError, torch.AcceleratorError) as e:
            logger.warning(f"清理CUDA显存时出错: {e}")
        
        # 清理内存
        gc.collect()
        
        logger.info("模型工作进程已退出并清理资源")

# 工作进程内部的模型加载函数
def _load_zimage_t2i_model_worker(params):
    """工作进程内部加载z-image文生图模型"""
    from modelscope import ZImagePipeline
    import torch
    
    cpu_offload = _is_cpu_offload_enabled_image_worker()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.bfloat16
    model_path = params.get('model_path', os.path.join(config.MODEL_DIR, "Z-Image-Turbo"))
    pipe = ZImagePipeline.from_pretrained(
        model_path,
        torch_dtype=torch_dtype
    )
    # pipe.transformer.set_attention_backend("flash")
    
    # 启用CPU卸载（节省显存）
    if cpu_offload:
        pipe.enable_model_cpu_offload()
    else:
        pipe.to(device)
    
    return pipe

def _load_qwen_i2i_model_worker(params):
    """工作进程内部加载qwen图生图模型"""
    import math
    from diffusers import (
        QwenImageEditPlusPipeline,
        QwenImageTransformer2DModel,
        FlowMatchEulerDiscreteScheduler,
    )
    from transformers import Qwen2_5_VLForConditionalGeneration, Qwen2Tokenizer
    import torch

    cpu_offload = _is_cpu_offload_enabled_image_worker()
    model_path = params.get('model_path', os.path.join(config.MODEL_DIR, "Qwen-Image-Edit-2509-4bit"))
    # 设备配置
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.bfloat16

    # 加载模型组件
    transformer = QwenImageTransformer2DModel.from_pretrained(
        model_path,
        subfolder="transformer",
        torch_dtype=torch_dtype
    )
    transformer = transformer.to("cpu")

    # 加载 text_encoder
    text_encoder = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_path,
        subfolder="text_encoder",
        dtype=torch_dtype
    )
    text_encoder = text_encoder.to("cpu")

    # 加载调度器
    scheduler_config = {
        "base_image_seq_len": 256,
        "base_shift": math.log(3),
        "invert_sigmas": False,
        "max_image_seq_len": 8192,
        "max_shift": math.log(3),
        "num_train_timesteps": 1000,
        "shift": 1.0,
        "shift_terminal": None,
        "stochastic_sampling": False,
        "time_shift_type": "exponential",
        "use_beta_sigmas": False,
        "use_dynamic_shifting": True,
        "use_exponential_sigmas": False,
        "use_karras_sigmas": False,
    }
    scheduler = FlowMatchEulerDiscreteScheduler.from_config(scheduler_config)

    pipe = QwenImageEditPlusPipeline.from_pretrained(
        model_path,
        local_files_only=True,
        torch_dtype=torch_dtype,
        transformer=transformer,
        text_encoder=text_encoder,
        scheduler=scheduler
    )

    pipe.set_progress_bar_config(disable=None)
    # 启用CPU卸载（节省显存）
    if cpu_offload:
        pipe.enable_model_cpu_offload()
    else:
        pipe.to(device)

    pipe.transformer.set_attention_backend("flash")
    pipe.vae.enable_slicing()
    pipe.vae.enable_tiling()
    pipe.safety_checker = None
    pipe.feature_extractor = None

    return pipe

def _load_wan_t2v_model_worker(params, lora_configs: Optional[list[LoraConfig]] = None):
    """工作进程内部加载wan文生视频模型"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        logging.info("开始导入 utils.wan")
        from utils.wan import WanModelPipeRunner
        logging.info("utils.wan 导入成功")
    except Exception as e:
        logging.error(f"导入 utils.wan 失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    model_path = params.get('model_path', os.path.join(config.MODEL_DIR, "Wan2.1-Distill-Models"))
    model_config_path = params.get('model_config_path', os.path.join(config.WAN_MODEL_CONFIG_DIR, "wan_t2v_distill_4step_cfg.json"))
    model_cls = params.get('model_cls', "wan2.1_distill")
    
    logging.info(f"模型加载参数: model_path={model_path}, model_config_path={model_config_path}, model_cls={model_cls}")
    
    try:
        # 格式化lora_configs
        formatted_lora_configs = _format_lora_configs(lora_configs)
        logger.info(f"导入模型lora配置: {formatted_lora_configs}")
        pipe = WanModelPipeRunner(
            model_path=model_path,
            config_json_path=model_config_path,
            model_cls=model_cls,
            task="t2v",
            lora_configs=formatted_lora_configs
        )
        logging.info("WanModelPipeRunner 初始化成功")
        
        logging.info("开始加载模型...")
        pipe.load()
        logging.info("模型加载成功")
        return pipe
    except Exception as e:
        logging.error(f"模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        raise

def _load_wan_i2v_model_worker(params, lora_configs: Optional[list[LoraConfig]] = None):
    """工作进程内部加载wan图生视频模型"""
    from utils.wan import WanModelPipeRunner
    
    model_path = params.get('model_path', os.path.join(config.MODEL_DIR, "Wan2.2-Distill-Models"))
    model_config_path = params.get('model_config_path', os.path.join(config.WAN_MODEL_CONFIG_DIR, "wan_moe_i2v_distill.json"))
    model_cls = params.get('model_cls', "wan2.2_moe_distill")
    
    # 格式化lora_configs
    formatted_lora_configs = _format_lora_configs(lora_configs)
    logger.info(f"导入模型lora配置: {formatted_lora_configs}")
    logger.info(f"导入模型lora配置: {formatted_lora_configs}")
    pipe = WanModelPipeRunner(
        model_path=model_path,
        config_json_path=model_config_path,
        model_cls=model_cls,
        task="i2v",
        lora_configs=formatted_lora_configs
    )
    pipe.load()
    return pipe

def _is_cpu_offload_enabled_image_worker() -> bool:
    import torch
    """工作进程内部判断是否需要开启 CPU 卸载功能"""
    if not torch.cuda.is_available():
        return False
    
    gpu_count = torch.cuda.device_count()
    main_gpu_index = 0
    if main_gpu_index >= gpu_count:
        return False
    
    gpu_properties = torch.cuda.get_device_properties(main_gpu_index)
    total_memory_bytes = gpu_properties.total_memory
    total_memory_gb = total_memory_bytes / (1024 ** 3)
    
    return total_memory_gb < 32.0

class ModelScheduler:
    """基于进程隔离的模型调度器，管理qwen和wan模型的加载和卸载"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelScheduler, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        """初始化模型调度器"""
        self.current_task = None  # 当前模型的任务类型
        self.model_params = {}  # 当前模型的参数
        self.current_lora_configs = None  # 当前模型的LoRA配置
        
        # 进程相关
        self.model_process = None  # 模型工作进程
        self.task_queue = None  # 任务队列
        self.result_queue = None  # 结果队列
        
        # 确保multiprocessing以spawn模式启动（支持CUDA的多进程使用）
        mp.set_start_method('spawn', force=True)

    def is_cpu_offload_enabled_image(self) -> bool:
        import torch
        """
        判断是否需要开启 CPU 卸载功能
        判定条件：若存在可用 NVIDIA GPU 且其显存小于 32GB，则返回 True（开启 CPU 卸载）；否则返回 False（不开启）

        Returns:
            bool: True - 开启 CPU 卸载；False - 不开启 CPU 卸载
        """
        # 1. 先判断是否有可用的 NVIDIA GPU
        if not torch.cuda.is_available():
            # 无 GPU 时，默认无需开启 CPU 卸载（或根据业务需求调整，此处返回 False）
            print("提示：未检测到可用 NVIDIA GPU，无需开启 CPU 卸载")
            return False

        # 2. 获取当前 GPU 设备数量（多 GPU 场景取主 GPU（索引 0）的显存进行判断）
        gpu_count = torch.cuda.device_count()
        main_gpu_index = 0  # 主 GPU 索引，默认取第 0 块
        if main_gpu_index >= gpu_count:
            print("提示：主 GPU 索引超出可用范围，无需开启 CPU 卸载")
            return False

        # 3. 获取主 GPU 的显存信息（单位：字节 Byte）
        # torch.cuda.get_device_properties 返回 GPU 设备属性对象
        gpu_properties = torch.cuda.get_device_properties(main_gpu_index)
        total_memory_bytes = gpu_properties.total_memory  # 总显存（字节）

        # 4. 单位转换：字节（Byte）→ 吉字节（GB，1GB = 1024^3 Byte = 1073741824 Byte）
        # 注：若需按 1GB=1000^3 Byte 计算，可替换为 1000**3
        total_memory_gb = total_memory_bytes / (1024 ** 3)

        # 5. 判断显存是否小于 32GB，返回对应结果
        if total_memory_gb < 32.0:
            print(f"提示：主 GPU（索引 {main_gpu_index}）显存为 {total_memory_gb:.2f} GB（< 32GB），建议开启 CPU 卸载")
            return True
        else:
            print(f"提示：主 GPU（索引 {main_gpu_index}）显存为 {total_memory_gb:.2f} GB（≥ 32GB），无需开启 CPU 卸载")
            return False

    def _create_model_process(self):
        """创建模型工作进程"""
        logger.info("创建模型工作进程")
        
        # 创建进程间通信队列
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        
        # 创建并启动工作进程
        self.model_process = mp.Process(
            target=model_worker_process,
            args=(self.task_queue, self.result_queue)
        )
        self.model_process.daemon = True  # 设置为守护进程
        self.model_process.start()
        
        logger.info(f"模型工作进程已启动，PID: {self.model_process.pid}")
    
    def _terminate_model_process(self):
        """终止模型工作进程"""
        if self.model_process is not None and self.model_process.is_alive():
            logger.info(f"终止模型工作进程，PID: {self.model_process.pid}")
            
            # 尝试优雅退出
            try:
                self.task_queue.put(ModelMessage('exit'))
                # 等待进程退出
                self.model_process.join(timeout=5)
            except Exception as e:
                logger.warning(f"优雅终止模型工作进程失败: {e}")
            
            # 强制终止
            if self.model_process.is_alive():
                logger.warning("模型工作进程未能优雅退出，将强制终止")
                self.model_process.terminate()
                self.model_process.join(timeout=3)
            
            # 清理队列和进程引用
            self.task_queue = None
            self.result_queue = None
            self.model_process = None
        
        self.current_task = None
        self.model_params = {}
        self.current_lora_configs = None
        logger.info("模型工作进程已终止")
    
    def _send_message(self, msg, timeout=60):
        """发送消息到模型工作进程并等待结果"""
        if self.model_process is None or not self.model_process.is_alive():
            raise RuntimeError("模型工作进程未启动")
        
        # 发送消息
        self.task_queue.put(msg)
        
        # 等待结果
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError("等待模型工作进程响应超时")
            
            if not self.result_queue.empty():
                return self.result_queue.get()
            
            # 检查进程是否还在运行
            if not self.model_process.is_alive():
                # 尝试从队列中获取错误信息
                error_message = "模型工作进程已意外退出"
                try:
                    if not self.result_queue.empty():
                        error_msg = self.result_queue.get()
                        if error_msg.msg_type == 'error':
                            error_message = error_msg.error
                except:
                    pass
                raise RuntimeError(error_message)
            
            time.sleep(0.1)

    def load_model(self, task_type, lora_configs: Optional[list[LoraConfig]] = None, **kwargs):
        """
        加载指定类型的模型
        
        Args:
            task_type: str, 任务类型 ('text2img', 'img2img', 'text2video', 'img2video')
            lora_configs: Optional[list[LoraConfig]], LoRA配置列表
            **kwargs: 模型加载参数
            
        Returns:
            Callable: 模型推理函数
        """
        # 支持的任务类型
        supported_tasks = ['text2img', 'img2img', 'text2video', 'img2video']
        
        # 验证任务类型
        if task_type not in supported_tasks:
            raise ValueError(f"不支持的任务类型: {task_type}")
        
        logger.info(f"加载模型, 任务类型: {task_type}, LoRA配置: {lora_configs}, 参数: {kwargs}")
        
        # 检查是否需要加载新模型
        if self.current_task == task_type:
            # 检查LoRA配置是否相同
            lora_configs_match = False
            
            # 如果传过来的lora_configs是None，则当前的current_lora_configs也需要是None才复用
            if lora_configs is None:
                if self.current_lora_configs is None:
                    lora_configs_match = True
            # 否则，检查两个列表是否相同
            else:
                if self.current_lora_configs is not None and len(lora_configs) == len(self.current_lora_configs):
                    lora_configs_match = all(
                        cfg1.get('path') == cfg2.get('path') and cfg1.get('strength') == cfg2.get('strength')
                        for cfg1, cfg2 in zip(lora_configs, self.current_lora_configs)
                    )
            
            if lora_configs_match:
                logger.info(f"模型 (任务: {task_type}, LoRA配置: {lora_configs}) 已加载，直接复用")
                return self._get_inference_func()
        
        # 如果当前有模型且任务类型不同或LoRA配置不同，则卸载当前模型
        if self.current_task is not None:
            self.unload_model()
        
        # 加载新模型
        max_retries = 2
        for retry in range(max_retries):
            try:
                # 创建模型工作进程（如果尚未创建）
                if self.model_process is None or not self.model_process.is_alive():
                    self._create_model_process()
                
                # 将lora_configs添加到params中
                kwargs_with_lora = kwargs.copy()
                if lora_configs:
                    kwargs_with_lora['lora_configs'] = lora_configs
                
                # 发送加载模型消息
                msg = ModelMessage('load', task_type, params=kwargs_with_lora)
                result_msg = self._send_message(msg, timeout=600)  # 增加超时时间
                
                if result_msg.msg_type == 'error':
                    raise RuntimeError(f"模型加载失败: {result_msg.error}")
                
                self.current_task = task_type
                self.model_params = kwargs
                self.current_lora_configs = lora_configs
                logger.info(f"模型 (任务: {self.current_task}, LoRA配置: {self.current_lora_configs}) 加载成功")
                return self._get_inference_func()
                
            except RuntimeError as e:
                if "模型工作进程已意外退出" in str(e) and retry < max_retries - 1:
                    logger.warning(f"模型工作进程意外退出，正在重启并尝试重新加载模型 (尝试 {retry + 1}/{max_retries})")
                    self._terminate_model_process()
                    # 清理状态
                    self.current_task = None
                    self.model_params = {}
                    self.current_lora_configs = None
                    # 继续循环，尝试重新加载
                    continue
                else:
                    logger.exception(f"加载模型失败: {e}")
                    self._terminate_model_process()
                    raise  # 重新抛出异常，确保调用者知道模型加载失败
    
    def _get_inference_func(self):
        """获取模型推理函数"""
        def inference(**kwargs):
            """模型推理函数"""
            if self.model_process is None or not self.model_process.is_alive():
                raise RuntimeError("模型工作进程未运行")
            
            # 发送推理消息
            msg = ModelMessage('run', self.current_task, params=kwargs)
            result_msg = self._send_message(msg, timeout=600)  # 增加推理超时时间
            
            if result_msg.msg_type == 'error':
                # 如果推理失败，终止进程并抛出异常
                logger.warning(f"推理失败，将终止模型进程: {result_msg.error}")
                self._terminate_model_process()
                raise RuntimeError(f"模型推理失败: {result_msg.error}")
            
            return result_msg.result
        
        return inference
    
    def get_gpu_memory_info(self):
        import torch
        """
        获取GPU内存使用信息
        
        Returns:
            dict: 包含总内存、已用内存和可用内存的字典（单位：GB）
        """
        if not torch.cuda.is_available():
            return {}
        
        # 获取当前设备
        device = torch.cuda.current_device()
        
        # 获取GPU属性
        props = torch.cuda.get_device_properties(device)
        total_memory_gb = props.total_memory / (1024 ** 3)
        
        # 获取内存使用情况
        memory_allocated = torch.cuda.memory_allocated(device) / (1024 ** 3)
        memory_reserved = torch.cuda.memory_reserved(device) / (1024 ** 3)
        
        return {
            'total': total_memory_gb,
            'allocated': memory_allocated,
            'reserved': memory_reserved,
            'available': total_memory_gb - memory_reserved
        }
    
    def get_cpu_memory_usage(self):
        """
        获取CPU内存使用情况
        
        Returns:
            dict: 包含已用内存和可用内存的字典（单位：GB）
        """
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        mem_used = mem_info.rss / (1024 ** 3)  # 已用内存（GB）
        
        # 获取系统总内存和可用内存
        virtual_mem = psutil.virtual_memory()
        total_mem = virtual_mem.total / (1024 ** 3)
        available_mem = virtual_mem.available / (1024 ** 3)
        
        return {
            'process_used': mem_used,
            'system_total': total_mem,
            'system_available': available_mem
        }
    
    def unload_model(self):
        """
        卸载当前模型，释放显存和内存
        通过终止模型工作进程来确保完全释放内存和显存
        """
        if self.current_task is None:
            return
        
        # 卸载前记录内存使用情况
        gpu_memory_before = self.get_gpu_memory_info()
        cpu_memory_before = self.get_cpu_memory_usage()
        logger.info(f"卸载当前模型前GPU内存使用: {gpu_memory_before}")
        logger.info(f"卸载当前模型前CPU内存使用: {cpu_memory_before}")
        logger.info(f"卸载当前模型 (任务: {self.current_task})")
        
        # 终止模型工作进程
        self._terminate_model_process()
        
        # 清理Python引用和CPU内存
        gc.collect()
        
        # 卸载后记录内存使用情况
        gpu_memory_after = self.get_gpu_memory_info()
        cpu_memory_after = self.get_cpu_memory_usage()
        logger.info(f"卸载当前模型后GPU内存使用: {gpu_memory_after}")
        logger.info(f"卸载当前模型后CPU内存使用: {cpu_memory_after}")
        
        # 计算内存释放量
        if 'reserved' in gpu_memory_before and 'reserved' in gpu_memory_after:
            gpu_memory_freed = gpu_memory_before['reserved'] - gpu_memory_after['reserved']
            logger.info(f"GPU内存释放: {gpu_memory_freed:.2f} GB")
        
        if 'process_used' in cpu_memory_before and 'process_used' in cpu_memory_after:
            cpu_memory_freed = cpu_memory_before['process_used'] - cpu_memory_after['process_used']
            logger.info(f"CPU内存释放: {cpu_memory_freed:.2f} GB")
        
        logger.info("模型卸载完成，显存和内存已释放")
    
    def get_current_model(self):
        """
        获取当前加载的模型信息
        
        Returns:
            dict: 当前模型信息
        """
        return {
            'current_task': self.current_task,
            'model_params': self.model_params,
            'process_pid': self.model_process.pid if self.model_process is not None and self.model_process.is_alive() else None
        }
    
    def clear(self):
        """清理模型调度器"""
        self.unload_model()

# 创建全局模型调度器实例
model_scheduler = ModelScheduler()