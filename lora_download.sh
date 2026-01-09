LORA_DIR="/home/ubuntu/loras"

# qwen
modelscope download --model flymy-ai/qwen-image-edit-2509-inscene-lora \
    --local_dir $LORA_DIR \
    --include "pytorch_lora_weights.safetensors"

# z_image
modelscope download --model AI-ModelScope/pixel_art_style_lora_z_image_turbo \
    --local_dir $LORA_DIR \
    --include "pixel_art_style_z_image_turbo.safetensors"

# wan2.1

# wan2.2
