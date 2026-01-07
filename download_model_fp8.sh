WAN_21_DISTILL_MODELS_DIR="/home/ubuntu/models/Wan2.1-Distill-Models"
WAN_22_DISTILL_MODELS_DIR="/home/ubuntu/models/Wan2.2-Distill-Models"
Z_IMAGE_MODEL_DIR="/home/ubuntu/models/Z-Image-Turbo"
QWEN_IMAGE_EDIT_MODEL_DIR="/home/ubuntu/models/Qwen-Image-Edit-2509-4bit"

# 下载Wan2.1-T2V-14B模型
mkdir -p $WAN_21_DISTILL_MODELS_DIR

modelscope download --model  lightx2v/Wan2.1-Distill-Models \
    --local_dir $WAN_21_DISTILL_MODELS_DIR \
    --include "wan2.1_t2v_14b_scaled_fp8_e4m3_lightx2v_4step.safetensors"

modelscope download --model  lightx2v/Wan2.1-Distill-Models \
    --local_dir $WAN_21_DISTILL_MODELS_DIR \
    --include "config.json"

modelscope download --model  Wan-AI/Wan2.1-T2V-14B \
    --local_dir $WAN_21_DISTILL_MODELS_DIR \
    --include "Wan2.1_VAE.pth"

modelscope download --model lightx2v/Encoders \
    --local_dir $WAN_21_DISTILL_MODELS_DIR \
    --include "models_t5_umt5-xxl-enc-fp8.pth"

modelscope download --model lightx2v/Encoders \
    --local_dir $WAN_21_DISTILL_MODELS_DIR \
    --include "models_clip_open-clip-xlm-roberta-large-vit-huge-14-fp8.pth"

modelscope download --model lightx2v/Encoders \
    --local_dir $WAN_21_DISTILL_MODELS_DIR \
    --include "google/**/*"


# 下载Wan2.2-I2V-A14B模型
WAN_22_HIGH_NOISE_DIR="$WAN_22_DISTILL_MODELS_DIR/high_noise_model"
WAN_22_LOW_NOISE_DIR="$WAN_22_DISTILL_MODELS_DIR/low_noise_model"
mkdir -p $WAN_22_DISTILL_MODELS_DIR
mkdir -p $WAN_22_HIGH_NOISE_DIR
mkdir -p $WAN_22_LOW_NOISE_DIR

modelscope download --model  lightx2v/Wan2.2-Distill-Models \
    --local_dir $WAN_22_HIGH_NOISE_DIR \
    --include "wan2.2_i2v_A14b_high_noise_scaled_fp8_e4m3_lightx2v_4step.safetensors"

modelscope download --model  lightx2v/Wan2.2-Distill-Models \
    --local_dir $WAN_22_LOW_NOISE_DIR \
    --include "wan2.2_i2v_A14b_low_noise_scaled_fp8_e4m3_lightx2v_4step.safetensors"

modelscope download --model  lightx2v/Wan2.2-Distill-Models \
    --local_dir $WAN_22_DISTILL_MODELS_DIR \
    --include "config.json"

modelscope download --model  Wan-AI/Wan2.2-I2V-A14B \
    --local_dir $WAN_22_DISTILL_MODELS_DIR \
    --include "Wan2.1_VAE.pth"

modelscope download --model lightx2v/Encoders \
    --local_dir $WAN_21_DISTILL_MODELS_DIR \
    --include "models_t5_umt5-xxl-enc-fp8.pth"

modelscope download --model lightx2v/Encoders \
    --local_dir $WAN_21_DISTILL_MODELS_DIR \
    --include "google/**/*"


mkdir -p $Z_IMAGE_MODEL_DIR
modelscope download --model Tongyi-MAI/Z-Image-Turbo \
 --local_dir $Z_IMAGE_MODEL_DIR


mkdir -p $QWEN_IMAGE_EDIT_MODEL_DIR
# huggingface-cli download ovedrive/Qwen-Image-Edit-2509-4bit \
#  --local-dir $QWEN_IMAGE_EDIT_MODEL_DIR
hf download ovedrive/Qwen-Image-Edit-2509-4bit \
 --local-dir $QWEN_IMAGE_EDIT_MODEL_DIR