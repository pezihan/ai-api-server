WAN_21_DISTILL_MODELS_DIR="/home/ubuntu/models/Wan2.1-Distill-Models"
WAN_22_DISTILL_MODELS_DIR="/home/ubuntu/models/Wan2.2-Distill-Models"
QWEN_IMAGE_EDIT_MODEL_DIR="/home/ubuntu/models/Qwen-Image-Edit-2511-4bit"
Z_IMAGE_MODEL_DIR="/home/ubuntu/models/Z-Image-Turbo"

PU_MPDEL="/models"


mkdir -p $WAN_21_DISTILL_MODELS_DIR
ln -s $PU_MPDEL/ModelScope/lightx2v/Wan2.1-Distill-Models/wan2.1_t2v_14b_scaled_fp8_e4m3_lightx2v_4step.safetensors $WAN_21_DISTILL_MODELS_DIR/wan2.1_t2v_14b_scaled_fp8_e4m3_lightx2v_4step.safetensors

ln -s $PU_MPDEL/ModelScope/lightx2v/Wan2.1-Distill-Models/config.json $WAN_21_DISTILL_MODELS_DIR/config.json

ln -s $PU_MPDEL/ModelScope/Wan-AI/Wan2.1-T2V-14B/Wan2.1_VAE.pth $WAN_21_DISTILL_MODELS_DIR/Wan2.1_VAE.pth

ln -s $PU_MPDEL/ModelScope/lightx2v/Encoders/models_t5_umt5-xxl-enc-fp8.pth $WAN_21_DISTILL_MODELS_DIR/models_t5_umt5-xxl-enc-fp8.pth

ln -s $PU_MPDEL/ModelScope/lightx2v/Encoders/models_clip_open-clip-xlm-roberta-large-vit-huge-14-fp8.pth $WAN_21_DISTILL_MODELS_DIR/models_clip_open-clip-xlm-roberta-large-vit-huge-14-fp8.pth

sh link_files.sh $PU_MPDEL/ModelScope/lightx2v/Encoders/google $WAN_21_DISTILL_MODELS_DIR/google


# 下载Wan2.2-I2V-A14B模型
WAN_22_HIGH_NOISE_DIR="$WAN_22_DISTILL_MODELS_DIR/high_noise_model"
WAN_22_LOW_NOISE_DIR="$WAN_22_DISTILL_MODELS_DIR/low_noise_model"
mkdir -p $WAN_22_DISTILL_MODELS_DIR
mkdir -p $WAN_22_HIGH_NOISE_DIR
mkdir -p $WAN_22_LOW_NOISE_DIR


ln -s $PU_MPDEL/HuggingFace/lightx2v/Wan2.2-Distill-Models/wan2.2_i2v_A14b_high_noise_scaled_fp8_e4m3_lightx2v_4step.safetensors $WAN_22_HIGH_NOISE_DIR/wan2.2_i2v_A14b_high_noise_scaled_fp8_e4m3_lightx2v_4step.safetensors


ln -s $PU_MPDEL/HuggingFace/lightx2v/Wan2.2-Distill-Models/wan2.2_i2v_A14b_low_noise_scaled_fp8_e4m3_lightx2v_4step.safetensors $WAN_22_LOW_NOISE_DIR/wan2.2_i2v_A14b_low_noise_scaled_fp8_e4m3_lightx2v_4step.safetensors


ln -s $PU_MPDEL/HuggingFace/lightx2v/Wan2.2-Distill-Models/config.json $WAN_22_DISTILL_MODELS_DIR/config.json


ln -s $PU_MPDEL/HuggingFace/Wan-AI/Wan2.2-I2V-A14B/Wan2.1_VAE.pth $WAN_22_DISTILL_MODELS_DIR/Wan2.1_VAE.pth


ln -s $PU_MPDEL/HuggingFace/lightx2v/Encoders/models_t5_umt5-xxl-enc-fp8.pth $WAN_22_DISTILL_MODELS_DIR/models_t5_umt5-xxl-enc-fp8.pth

sh link_files.sh $PU_MPDEL/ModelScope/lightx2v/Encoders/google $WAN_22_DISTILL_MODELS_DIR/google

mkdir -p $Z_IMAGE_MODEL_DIR
sh link_files.sh $PU_MPDEL/ModelScope/Tongyi-MAI/Z-Image-Turbo $Z_IMAGE_MODEL_DIR

mkdir -p $QWEN_IMAGE_EDIT_MODEL_DIR
sh link_files.sh $PU_MPDEL/HuggingFace/ovedrive/Qwen-Image-Edit-2511-4bit $QWEN_IMAGE_EDIT_MODEL_DIR
