import torch
import os
import gc
import sys
import traceback
import multiprocessing as mp
import time
from utils.logger import logger
from config.config import config

# Set PyTorch CUDA memory allocation configuration to avoid fragmentation
if torch.cuda.is_available():
    os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')

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
            msg = task_queue.get()
            
            if msg.msg_type == 'exit':
                logger.info("收到退出消息，模型工作进程将退出")
                break
            
            elif msg.msg_type == 'load':
                # 加载模型
                try:
                    logger.info(f"模型工作进程加载模型: {msg.task_type}")
                    
                    # 根据任务类型加载不同模型
                    if msg.task_type == 'text2img':
                        model_pipeline = _load_zimage_t2i_model_worker(msg.params)
                    elif msg.task_type == 'img2img':
                        model_pipeline = _load_qwen_i2i_model_worker(msg.params)
                    elif msg.task_type == 'text2video':
                        model_pipeline = _load_wan_t2v_model_worker(msg.params)
                    elif msg.task_type == 'img2video':
                        model_pipeline = _load_wan_i2v_model_worker(msg.params)
                    
                    current_task = msg.task_type
                    logger.info(f"模型 (任务: {current_task}) 加载成功")
                    result_queue.put(ModelMessage('result', msg.task_type, result="success"))
                except Exception as e:
                    logger.exception(f"模型工作进程加载模型失败: {e}")
                    result_queue.put(ModelMessage('error', msg.task_type, error=str(e)))
            
            elif msg.msg_type == 'run':
                # 运行模型
                try:
                    logger.info(f"模型工作进程运行任务: {msg.task_type}")
                    if model_pipeline is None:
                        raise RuntimeError("模型未加载")
                    
                    # 执行推理
                    if hasattr(model_pipeline, 'infer'):
                        result = model_pipeline.infer(**msg.params)
                    else:
                        result = model_pipeline(**msg.params)
                    logger.info(f"模型工作进程任务完成: {msg.task_type}")
                    result_queue.put(ModelMessage('result', msg.task_type, result=result))
                except Exception as e:
                    logger.error(f"模型工作进程运行任务失败: {e}\n{traceback.format_exc()}")
                    result_queue.put(ModelMessage('error', msg.task_type, error=str(e)))
            
            elif msg.msg_type == 'unload':
                # 卸载模型
                try:
                    logger.info(f"模型工作进程卸载模型: {current_task}")
                    if model_pipeline is not None:
                        if hasattr(model_pipeline, 'cleanup'):
                            model_pipeline.cleanup()
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
                    logger.exception(f"模型工作进程卸载模型失败: {e}")
                    result_queue.put(ModelMessage('error', msg.task_type, error=str(e)))
    
    except Exception as e:
        logger.exception(f"模型工作进程异常退出: {e}")
    finally:
        # 清理资源
        if model_pipeline is not None:
            del model_pipeline
        
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
    pipe.transformer.set_attention_backend("flash")
    
    # 启用CPU卸载（节省显存）
    if cpu_offload:
        pipe.enable_model_cpu_offload()
    else:
        pipe.to(device)
    
    return pipe

def _load_qwen_i2i_model_worker(params):
    """工作进程内部加载qwen图生图模型"""
    from modelscope import QwenImageEditPlusPipeline, QwenImageTransformer2DModel
    import torch
    from transformers import Qwen2_5_VLForConditionalGeneration

    cpu_offload = _is_cpu_offload_enabled_image_worker()
    model_path = params.get('model_path', os.path.join(config.MODEL_DIR, "Qwen-Image-Edit-2509-4bit"))
    
    # 设备配置
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.bfloat16

    transformer = QwenImageTransformer2DModel.from_pretrained(
        model_path,
        subfolder="transformer",
        torch_dtype=torch_dtype
    )
    text_encoder = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_path,
        subfolder="text_encoder",
        dtype=torch_dtype
    )

    pipe = QwenImageEditPlusPipeline.from_pretrained(
        model_path,
        local_files_only=True,
        torch_dtype=torch_dtype,
        transformer=transformer,
        text_encoder=text_encoder
    )
    
    pipe.set_progress_bar_config(disable=None)
    # 启用CPU卸载（节省显存）
    if cpu_offload:
        pipe.enable_model_cpu_offload()
    else:
        pipe.to(device)

    pipe.transformer.set_attention_backend("flash")
    
    return pipe

def _load_wan_t2v_model_worker(params):
    """工作进程内部加载wan文生视频模型"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        logging.info("开始导入 utils.wan")
        from utils.wan import WanPipeRunner
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
        pipe = WanPipeRunner(
            model_path=model_path,
            config_json_path=model_config_path,
            model_cls=model_cls,
            task="t2v"
        )
        logging.info("WanPipeRunner 初始化成功")
        
        logging.info("开始加载模型...")
        pipe.load()
        logging.info("模型加载成功")
        return pipe
    except Exception as e:
        logging.error(f"模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        raise

def _load_wan_i2v_model_worker(params):
    """工作进程内部加载wan图生视频模型"""
    from utils.wan import WanPipeRunner
    
    model_path = params.get('model_path', os.path.join(config.MODEL_DIR, "Wan2.2-Distill-Models"))
    model_config_path = params.get('model_config_path', os.path.join(config.WAN_MODEL_CONFIG_DIR, "wan_moe_i2v_distill.json"))
    model_cls = params.get('model_cls', "wan2.2_moe")
    
    pipe = WanPipeRunner(
        model_path=model_path,
        config_json_path=model_config_path,
        model_cls=model_cls,
        task="i2v"
    )
    pipe.load()
    return pipe

def _is_cpu_offload_enabled_image_worker() -> bool:
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
        
        # 进程相关
        self.model_process = None  # 模型工作进程
        self.task_queue = None  # 任务队列
        self.result_queue = None  # 结果队列
        
        # 确保multiprocessing以spawn模式启动（支持CUDA的多进程使用）
        mp.set_start_method('spawn', force=True)

    def is_cpu_offload_enabled_image(self) -> bool:
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
                raise RuntimeError("模型工作进程已意外退出")
            
            time.sleep(0.1)

    def load_model(self, task_type, **kwargs):
        """
        加载指定类型的模型
        
        Args:
            task_type: str, 任务类型 ('text2img', 'img2img', 'text2video', 'img2video')
            **kwargs: 模型加载参数
            
        Returns:
            Callable: 模型推理函数
        """
        # 支持的任务类型
        supported_tasks = ['text2img', 'img2img', 'text2video', 'img2video']
        
        # 验证任务类型
        if task_type not in supported_tasks:
            raise ValueError(f"不支持的任务类型: {task_type}")
        
        logger.info(f"加载模型, 任务类型: {task_type}, 参数: {kwargs}")
        
        # 检查是否需要加载新模型
        if self.current_task == task_type:
            logger.info(f"模型 (任务: {task_type}) 已加载，直接复用")
            return self._get_inference_func()
        
        # 如果当前有模型且任务类型不同，则卸载当前模型
        if self.current_task is not None:
            self.unload_model()
        
        # 加载新模型
        try:
            # 创建模型工作进程（如果尚未创建）
            if self.model_process is None or not self.model_process.is_alive():
                self._create_model_process()
            
            # 发送加载模型消息
            msg = ModelMessage('load', task_type, params=kwargs)
            result_msg = self._send_message(msg, timeout=600)  # 增加超时时间
            
            if result_msg.msg_type == 'error':
                raise RuntimeError(f"模型加载失败: {result_msg.error}")
            
            self.current_task = task_type
            self.model_params = kwargs
            logger.info(f"模型 (任务: {self.current_task}) 加载成功")
            return self._get_inference_func()
            
        except Exception as e:
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