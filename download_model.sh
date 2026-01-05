WAN_21_DISTILL_MODELS_DIR="/models/Wan2.1-Distill-Models"
WAN_22_DISTILL_MODELS_DIR="/models/Wan2.2-Distill-Models"
Z_IMAGE_MODEL_DIR="/models/Z-Image-Turbo"
QWEN_IMAGE_EDIT_MODEL_DIR="/models/Qwen-Image-Edit-2511"

# 下载Wan2.1-T2V-14B模型
mkdir -p $WAN_21_DISTILL_MODELS_DIR

huggingface-cli download lightx2v/Wan2.1-Distill-Models \
    --local-dir $WAN_21_DISTILL_MODELS_DIR \
    --include "wan2.1_t2v_14b_lightx2v_4step.safetensors"

huggingface-cli download lightx2v/Wan2.1-Distill-Models \
    --local-dir $WAN_21_DISTILL_MODELS_DIR \
    --include "config.json"

huggingface-cli download Wan-AI/Wan2.1-T2V-14B \
    --local-dir $WAN_21_DISTILL_MODELS_DIR \
    --include "Wan2.1_VAE.pth"

huggingface-cli download Wan-AI/Wan2.1-T2V-14B \
    --local-dir $WAN_21_DISTILL_MODELS_DIR \
    --include "models_t5_umt5-xxl-enc-bf16.pth"

huggingface-cli download Wan-AI/Wan2.1-T2V-14B \
    --local-dir $WAN_21_DISTILL_MODELS_DIR \
    --include "google/**/*"


# 下载Wan2.2-I2V-A14B模型
WAN_22_HIGH_NOISE_DIR="$WAN_22_DISTILL_MODELS_DIR/high_noise_model"
WAN_22_LOW_NOISE_DIR="$WAN_22_DISTILL_MODELS_DIR/low_noise_model"
mkdir -p $WAN_22_DISTILL_MODELS_DIR
mkdir -p $WAN_22_HIGH_NOISE_DIR
mkdir -p $WAN_22_LOW_NOISE_DIR

huggingface-cli download lightx2v/Wan2.2-Distill-Models \
    --local-dir $WAN_22_HIGH_NOISE_DIR \
    --include "wan2.2_i2v_A14b_high_noise_lightx2v_4step.safetensors"

huggingface-cli download lightx2v/Wan2.2-Distill-Models \
    --local-dir $WAN_22_LOW_NOISE_DIR \
    --include "wan2.2_i2v_A14b_low_noise_lightx2v_4step.safetensors"

huggingface-cli download lightx2v/Wan2.2-Distill-Models \
    --local-dir $WAN_22_DISTILL_MODELS_DIR \
    --include "config.json"

huggingface-cli download Wan-AI/Wan2.2-I2V-A14B \
    --local-dir $WAN_22_DISTILL_MODELS_DIR \
    --include "Wan2.1_VAE.pth"

huggingface-cli download Wan-AI/Wan2.2-I2V-A14B \
    --local-dir $WAN_22_DISTILL_MODELS_DIR \
    --include "models_t5_umt5-xxl-enc-bf16.pth"

huggingface-cli download Wan-AI/Wan2.2-I2V-A14B \
    --local-dir $WAN_22_DISTILL_MODELS_DIR \
    --include "google/**/*"

modelscope download --model Tongyi-MAI/Z-Image-Turbo \
 --local_dir $Z_IMAGE_MODEL_DIR

modelscope download --model Qwen/Qwen-Image-Edit-2511 \
 --local_dir $QWEN_IMAGE_EDIT_MODEL_DIR