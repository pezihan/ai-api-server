import torch
import os
import gc
import sys
from utils.logger import logger
from config.config import config

class ModelScheduler:
    """模型调度器，管理qwen和wan模型的加载和卸载，避免显存溢出"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelScheduler, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        """初始化模型调度器"""
        self.current_task = None  # 当前模型的任务类型: None, 'text2img', 'img2img', 'text2video', 'img2video'
        self.model_pipeline = None  # 当前模型的pipeline实例
        self.model_params = {}  # 当前模型的参数

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

    def load_model(self, task_type, **kwargs):
        """
        加载指定类型的模型
        
        Args:
            task_type: str, 任务类型 ('text2img', 'img2img', 'text2video', 'img2video')
            **kwargs: 模型加载参数
            
        Returns:
            pipeline: 加载的模型pipeline实例
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
            return self.model_pipeline
        
        
        # 如果当前有模型且任务类型不同，则卸载当前模型
        if self.current_task is not None:
            self.unload_model()
        
        # 加载新模型
        try:
            if task_type == 'text2img':
                self._load_zimage_t2i_model(**kwargs)
            elif task_type == 'img2img':
                self._load_qwen_i2i_model(**kwargs)
            elif task_type == 'text2video':
                self._load_wan_t2v_model(**kwargs)
            elif task_type == 'img2video':
                self._load_wan_i2v_model(**kwargs)
            
            self.current_task = task_type
            self.model_params = kwargs
            logger.info(f"模型 (任务: {self.current_task}) 加载成功")
            return self.model_pipeline
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            # 如果是内存不足导致的失败，确保卸载当前模型
            if "CUDA out of memory" in str(e) or "memory" in str(e).lower():
                logger.warning(f"模型加载失败，可能是显存溢出导致，清理资源")
                self.unload_model()
            raise
    
    def _load_zimage_t2i_model(self, **kwargs):
        """加载z-image文生图模型"""
        import torch
        from modelscope import ZImagePipeline
        cpu_offload = self.is_cpu_offload_enabled_image()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.bfloat16
        model_path = kwargs.get('model_path', "Tongyi-MAI/Z-Image-Turbo")
        logger.info(f"加载z-image文生图模型: {model_path}")
        pipe = ZImagePipeline.from_pretrained(
            model_path,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=False,
        )
        pipe.transformer.set_attention_backend("flash")
        # 启用CPU卸载（节省显存）
        if cpu_offload:
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(device)
        
        self.model_pipeline = pipe
    
    def _load_qwen_i2i_model(self, **kwargs):
        """加载qwen图生图模型"""
        from diffusers import QwenImageEditPlusPipeline, QwenImageTransformer2DModel, FlowMatchEulerDiscreteScheduler
        from transformers import Qwen2_5_VLForConditionalGeneration
        import math

        cpu_offload = self.is_cpu_offload_enabled_image()
        model_path = kwargs.get('model_path', "Qwen/Qwen-Image-Edit-2511")
        max_side_length = kwargs.get('max_side_length', 896)
        use_lighting = kwargs.get('use_lighting', False)
        
        logger.info(f"加载qwen图生图模型: {model_path}, max_side_length: {max_side_length}, use_lighting: {use_lighting}")
        
        # 设备配置
        device = "cuda" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.bfloat16
        
        # 加载transformer组件
        transformer = QwenImageTransformer2DModel.from_pretrained(
            model_path,
            subfolder="transformer",
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=False
        )
        if cpu_offload:
            transformer = transformer.to("cpu")
        else:
            transformer.to(device)
        
        # 加载text_encoder组件
        text_encoder = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_path,
            subfolder="text_encoder",
            dtype=torch_dtype,
            low_cpu_mem_usage=False
        )
        if cpu_offload:
            text_encoder = text_encoder.to("cpu")
        else:
            text_encoder.to(device)
        
        # 加载调度器和pipeline
        if use_lighting:
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
        else:
            pipe = QwenImageEditPlusPipeline.from_pretrained(
                model_path,
                local_files_only=True,
                torch_dtype=torch_dtype,
                transformer=transformer,
                text_encoder=text_encoder
            )
        
        # 启用CPU卸载（节省显存）
        if cpu_offload:
            pipe.enable_model_cpu_offload()
            pipe.vae.enable_slicing()
            pipe.vae.enable_tiling()
            pipe.safety_checker = None
            pipe.feature_extractor = None
        else:
            pipe.to(device)
        
        self.model_pipeline = pipe
    
    def _load_wan_t2v_model(self, **kwargs):
        """加载wan文生视频模型"""
        # 将LightX2V目录添加到Python路径
        from wan import WanPipeRunner

        model_path = kwargs.get('model_path', os.path.join(config.WAN_MODEL_DIR, "Wan2.1-Distill-Models"))
        model_config_path = kwargs.get('model_config_path', os.path.join(config.WAN_MODEL_CONFIG_DIR, "wan_t2v_distill_4step_cfg.json"))
        model_cls = kwargs.get('model_cls', "wan2.1_distill")
        logger.info(f"加载wan文生视频模型: {model_path}, model_cls: {model_cls}")
        pipe = WanPipeRunner(
            model_path=model_path,
            config_json_path=model_config_path,
            model_cls=model_cls,
            task="t2v"
        )
        pipe.load()
        self.model_pipeline = pipe
    
    def _load_wan_i2v_model(self, **kwargs):
        """加载wan图生视频模型"""
        # 将LightX2V目录添加到Python路径
        from wan import WanPipeRunner

        model_path = kwargs.get('model_path', os.path.join(config.WAN_MODEL_DIR, "Wan2.2-Distill-Models"))
        model_config_path = kwargs.get('model_config_path', os.path.join(config.WAN_MODEL_CONFIG_DIR, "wan_moe_i2v_distill.json"))
        model_cls = kwargs.get('model_cls', "wan2.2_moe")
        
        logger.info(f"加载wan图生视频模型: {model_path}, model_cls: {model_cls}")
        
        # 初始化pipeline
        pipe = WanPipeRunner(
            model_path=model_path,
            config_json_path=model_config_path,
            model_cls=model_cls,
            task="i2v"
        )
        pipe.load()        
        self.model_pipeline = pipe
    
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
        """卸载当前模型，释放显存和内存"""
        if self.current_task is None:
            return
        
        # 卸载前记录内存使用情况
        gpu_memory_before = self.get_gpu_memory_info()
        cpu_memory_before = self.get_cpu_memory_usage()
        logger.info(f"卸载当前模型前GPU内存使用: {gpu_memory_before}")
        logger.info(f"卸载当前模型前CPU内存使用: {cpu_memory_before}")
        logger.info(f"卸载当前模型 (任务: {self.current_task})")
        
        # 释放模型资源 - 更彻底的清理
        if self.model_pipeline is not None:
            # 特殊处理wan模型，确保所有资源都被释放
            if hasattr(self.model_pipeline, 'cleanup'):
                try:
                    self.model_pipeline.cleanup()
                    logger.info("模型已执行自定义cleanup方法")
                except Exception as e:
                    logger.warning(f"执行模型cleanup方法时出错: {e}")
            
            # 释放所有可能的子组件
            for attr in dir(self.model_pipeline):
                if not attr.startswith('_'):
                    try:
                        obj = getattr(self.model_pipeline, attr)
                        if hasattr(obj, 'to') and callable(obj.to):
                            # 将模型组件移到CPU（如果不在CPU上）
                            if hasattr(obj, 'device') and obj.device.type == 'cuda':
                                obj.to('cpu')
                            # 清理组件的内部状态
                            if hasattr(obj, 'config'):
                                del obj.config
                            if hasattr(obj, 'state_dict'):
                                del obj.state_dict
                        # 尝试释放numpy数组等大对象
                        if hasattr(obj, '__array__') or hasattr(obj, 'numpy'):
                            try:
                                del obj
                            except Exception as e:
                                pass
                        else:
                            del obj
                    except Exception as e:
                        pass
            
            del self.model_pipeline
            self.model_pipeline = None
        
        # 清理GPU显存 - 多次尝试确保清理干净
        if torch.cuda.is_available():
            for i in range(3):
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
                # 短暂休眠让CUDA完成清理
                import time
                time.sleep(0.1)
        
        # 清理Python引用和CPU内存
        # 重置所有可能的全局引用
        import sys
        for module_name, module in list(sys.modules.items()):
            if module_name.startswith('diffusers') or module_name.startswith('transformers') or module_name.startswith('wan'):
                try:
                    # 清理模块中的全局变量
                    for attr in dir(module):
                        if not attr.startswith('__'):
                            try:
                                delattr(module, attr)
                            except Exception as e:
                                pass
                except Exception as e:
                    pass
        
        # 强制垃圾回收 - 多次回收确保彻底
        for i in range(3):
            gc.collect()
            # 调用循环收集器以处理循环引用
            gc.collect()
            import time
            time.sleep(0.2)
        
        self.current_task = None
        self.model_params = {}
        
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
            'model_pipeline': self.model_pipeline,
            'model_params': self.model_params
        }
    
    def clear(self):
        """清理模型调度器"""
        self.unload_model()

# 创建全局模型调度器实例
model_scheduler = ModelScheduler()