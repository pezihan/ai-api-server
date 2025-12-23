import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import math
import torch
from diffusers import (
    QwenImageEditPlusPipeline,
    QwenImageTransformer2DModel,
    FlowMatchEulerDiscreteScheduler,
)
from transformers import Qwen2_5_VLForConditionalGeneration, BitsAndBytesConfig
from PIL import Image

# ===================== 核心配置参数 =====================
model_path = "ovedrive/Qwen-Image-Edit-2509-4bit"
# 输出图片的最长边最大长度（核心新增参数）
max_side_length = 896  # 可根据需求调整，比如896、1280等
use_lighting = True
seed = 43
prompt = "雄伟壮观的山"
negative_prompt = "毁容，四肢畸形，多余的手指，过多的手指，糟糕的手，缺手指，模糊的脸，丑陋的脸，变异，变形，长脖子，裤子，多余的四肢，融合的手指"
# ======================================================

# 设备配置
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.bfloat16

def calculate_scaled_dimensions(image, max_side_length, multiple=8):
    """
    计算等比例缩放后的图片尺寸，保证：
    1. 最长边不超过max_side_length
    2. 宽高为multiple的整数倍（适配模型要求，通常为8）
    3. 最小尺寸不小于multiple（避免尺寸为0）
    
    Args:
        image: PIL Image对象
        max_side_length: 最长边的最大长度
        multiple: 尺寸需要满足的倍数（模型要求）
    
    Returns:
        int: 缩放后的宽度
        int: 缩放后的高度
    """
    original_width, original_height = image.size
    max_original_side = max(original_width, original_height)

    # 计算缩放比例
    if max_original_side <= max_side_length:
        scale = 1.0  # 无需缩放
    else:
        scale = max_side_length / max_original_side  # 等比例缩放

    # 计算基础缩放尺寸
    new_width = original_width * scale
    new_height = original_height * scale

    # 调整为multiple的整数倍（模型尺寸兼容性要求）
    new_width = round(new_width / multiple) * multiple
    new_height = round(new_height / multiple) * multiple

    # 确保最小尺寸合法
    new_width = max(new_width, multiple)
    new_height = max(new_height, multiple)

    return int(new_width), int(new_height)

# ===================== 加载模型组件 =====================
print('加载 transformer 组件')
transformer = QwenImageTransformer2DModel.from_pretrained(
    model_path,
    subfolder="transformer",
    torch_dtype=torch_dtype
)
transformer = transformer.to("cpu")

print('加载 text_encoder 组件')
text_encoder = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_path,
    subfolder="text_encoder",
    dtype=torch_dtype
)
text_encoder = text_encoder.to("cpu")

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
    print('加载 scheduler 组件')
    scheduler = FlowMatchEulerDiscreteScheduler.from_config(scheduler_config)
    
    print('加载 Qwen Image Edit Pipeline (带Lightning)')
    pipe = QwenImageEditPlusPipeline.from_pretrained(
        model_path,
        local_files_only=True,
        torch_dtype=torch_dtype,
        transformer=transformer,
        text_encoder=text_encoder,
        scheduler=scheduler
    )
    # 加载Lightning LoRA
    pipe.load_lora_weights(
        "./Qwen-Image-Edit-Remove-Clothes",
        weight_name="qwen-edit-remove-clothes.safetensors",
        adapter_name="clothes",
        scale=1.0
    )
else:
    print('加载 Qwen Image Edit Pipeline (基础版)')
    pipe = QwenImageEditPlusPipeline.from_pretrained(
        model_path,
        local_files_only=True,
        torch_dtype=torch_dtype,
        transformer=transformer,
        text_encoder=text_encoder
    )

# 启用CPU卸载（节省显存）
pipe.enable_model_cpu_offload()

pipe.vae.enable_slicing()
pipe.vae.enable_tiling()

pipe.safety_checker = None
pipe.feature_extractor = None

# ===================== 图片处理与生成 =====================
# 加载输入图片
input_image = Image.open("./ycy.jpeg").convert("RGB")
print(f"原始图片尺寸: {input_image.size}")

# 计算等比例缩放后的尺寸
scaled_width, scaled_height = calculate_scaled_dimensions(
    input_image, max_side_length
)
print(f"缩放后图片尺寸: {scaled_width} x {scaled_height}")

input_image = input_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

# 设置随机生成器
generator = torch.Generator(device=device).manual_seed(seed) if seed is not None else None

# 执行图片编辑生成
print("开始生成图片...")
with torch.inference_mode():
    output = pipe(
        image=input_image,
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=scaled_width,  # 使用缩放后的宽度
        height=scaled_height,  # 使用缩放后的高度
        num_inference_steps=6,
        true_cfg_scale=5.0,
        generator=generator,
    )

# 保存输出图片
output_image = output.images[0]
save_path = "output_image_edit.png"
output_image.save(save_path)
print(f"图片已保存至: {os.path.abspath(save_path)}")