import torch
import os
import gc
from utils.logger import logger

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
        self.current_model = None  # 当前加载的模型: None, 'qwen', 'wan'
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

    def load_model(self, model_type, **kwargs):
        """
        加载指定类型的模型
        
        Args:
            model_type: str, 模型类型 ('qwen' 或 'wan')
            **kwargs: 模型加载参数
            
        Returns:
            pipeline: 加载的模型pipeline实例
        """
        logger.info(f"加载模型: {model_type}, 参数: {kwargs}")
        
        # 如果要加载的模型与当前模型相同，直接返回
        if self.current_model == model_type:
            logger.info(f"模型 {model_type} 已加载，直接复用")
            return self.model_pipeline
        
        # 卸载当前模型
        self.unload_model()
        
        # 加载新模型
        try:
            if model_type == 'qwen':
                self._load_qwen_model(**kwargs)
            elif model_type == 'wan':
                self._load_wan_model(**kwargs)
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
            
            self.current_model = model_type
            self.model_params = kwargs
            logger.info(f"模型 {model_type} 加载成功")
            return self.model_pipeline
            
        except Exception as e:
            logger.error(f"加载模型 {model_type} 失败: {e}")
            raise
    
    def _load_qwen_model(self, **kwargs):
        """加载qwen图片生成模型"""
        from diffusers import QwenImageEditPlusPipeline, QwenImageTransformer2DModel, FlowMatchEulerDiscreteScheduler
        from transformers import Qwen2_5_VLForConditionalGeneration
        import math
        
        cpu_offload = self.is_cpu_offload_enabled_image()
        model_path = kwargs.get('model_path', "ovedrive/Qwen-Image-Edit-2509-4bit")
        max_side_length = kwargs.get('max_side_length', 896)
        use_lighting = kwargs.get('use_lighting', False)
        
        # 设备配置
        device = "cuda" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.bfloat16
        
        logger.info(f"加载qwen模型: {model_path}, max_side_length: {max_side_length}, use_lighting: {use_lighting}")
        
        # 加载transformer组件
        transformer = QwenImageTransformer2DModel.from_pretrained(
            model_path,
            subfolder="transformer",
            torch_dtype=torch_dtype
        )
        if cpu_offload:
            transformer = transformer.to("cpu")
        else:
            transformer.to(device)
        
        # 加载text_encoder组件
        text_encoder = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_path,
            subfolder="text_encoder",
            dtype=torch_dtype
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
    
    def _load_wan_model(self, **kwargs):
        """加载wan视频生成模型"""
        from ..LightX2V.lightx2v import LightX2VPipeline
        
        model_path = kwargs.get('model_path', "/path/to/Wan2.2-T2V-14B")
        model_cls = kwargs.get('model_cls', "wan2.2_moe")
        task = kwargs.get('task', "t2v")
        
        logger.info(f"加载wan模型: {model_path}, model_cls: {model_cls}, task: {task}")
        
        # 初始化pipeline
        pipe = LightX2VPipeline(
            model_path=model_path,
            model_cls=model_cls,
            task=task,
        )
        
        # 启用offload减少显存使用
        pipe.enable_offload(
            cpu_offload=True,
            offload_granularity="block",
            text_encoder_offload=True,
            image_encoder_offload=False,
            vae_offload=False,
        )
        
        self.model_pipeline = pipe
    
    def unload_model(self):
        """卸载当前模型，释放显存"""
        if self.current_model is None:
            return
        
        logger.info(f"卸载当前模型: {self.current_model}")
        
        # 释放模型资源
        if self.model_pipeline is not None:
            del self.model_pipeline
            self.model_pipeline = None
        
        # 清理GPU显存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        
        # 强制垃圾回收
        gc.collect()
        
        self.current_model = None
        self.model_params = {}
        
        logger.info("模型卸载完成，显存已释放")
    
    def get_current_model(self):
        """
        获取当前加载的模型信息
        
        Returns:
            dict: 当前模型信息
        """
        return {
            'model_type': self.current_model,
            'model_pipeline': self.model_pipeline,
            'model_params': self.model_params
        }
    
    def clear(self):
        """清理模型调度器"""
        self.unload_model()

# 创建全局模型调度器实例
model_scheduler = ModelScheduler()