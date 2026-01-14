# AI API Server

一个基于Flask的AI API服务，提供图像和视频生成功能，支持任务队列和文件管理。

## 功能特性

- 🖼️ **图像生成**：支持文本到图像（text2img）和图像到图像（img2img）生成
- 🎬 **视频生成**：支持文本到视频（text2video）和图像到视频（img2video）生成
- 📋 **任务队列**：使用Redis存储任务信息，RabbitMQ作为任务队列
- � **Docker支持**：提供Docker部署配置
- 🎨 **前端界面**：内置Vue前端，提供可视化操作界面
- 🚀 **模型加速**：支持Flash Attention等推理加速技术

## 快速开始

### 环境要求

- Python 3.11+
- Conda（推荐用于创建虚拟环境）
- GPU支持（用于图像和视频生成）
- 足够的磁盘空间（用于存储模型文件,至少120G）

### 1. 创建虚拟环境

```bash
conda create -n ai-server python=3.11 -y
conda activate ai-server
```

### 2. 安装依赖

```bash
# 安装API服务依赖
pip install -r requirements.api.txt -i https://mirrors.aliyun.com/pypi/simple/

# 安装任务执行器依赖
pip install -r requirements.worker.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 3. 安装LightX2V依赖

```bash
cd LightX2V
pip install -v -e . -i https://mirrors.aliyun.com/pypi/simple/
```

### 4. 安装推理加速

```bash
pip install flash-attn --no-build-isolation -i https://mirrors.aliyun.com/pypi/simple/

# 可选：从以下链接下载预编译的whl文件，省去编译的时间
# https://github.com/Dao-AILab/flash-attention/releases/tag/v2.8.3
# 下载完成后执行：pip install 对应的whl文件

# 推荐配置：python3.12 + torch2.8.0 + cuda12.1
# 例如：flash_attn-2.8.3+cu12torch2.8cxx11abiTRUE-cp312-cp312-linux_x86_64.whl
```

### 5. 安装FP8模型依赖（可选）
现在的默认配置里面使用的是fp8模型，所以这部必须操作
如果使用FP8模型，需要安装以下依赖：

```bash
pip install -r requirements.fp8.txt -i https://mirrors.aliyun.com/pypi/simple/

git clone https://github.com/KONAKONA666/q8_kernels
cd q8_kernels 
git submodule init
git submodule update
python setup.py install
pip install --no-build-isolation .
```

### 6. 下载模型文件

```bash
# 下载FP8大模型(默认)
bash download_model_fp8.sh
# 如果不使用fp8模型，执行下载普通模型命令，同时.env的WAN_TYPE配置设置成 WAN_TYPE=wan
bash download_model.sh

# 下载补帧模型
bash rife_download.sh
```

### 7. 配置环境变量

复制环境变量示例文件并根据需要修改：

```bash
cp .env.example .env
```

### 8. 启动服务

#### 方式一：Docker部署

```bash
# 启动所有服务（Redis、RabbitMQ、API服务、任务执行器）
docker-compose up -d
```

详细配置请参考`docker-compose.yml`文件。

#### 方式二：本地运行

1. **启动Redis和RabbitMQ**
   - 请参考各自官方文档安装并启动Redis和RabbitMQ

2. **启动任务队列消费者服务**
   ```bash
   python start_worker.py
   ```

3. **启动API服务**
   ```bash
   python api.py
   ```

## 项目结构

```
ai-api-server/
├── app/                     # Flask应用目录
│   ├── api/                 # API接口定义
│   │   ├── auth.py          # 认证接口
│   │   ├── health.py        # 健康检查接口
│   │   ├── image.py         # 图像生成接口
│   │   ├── video.py         # 视频生成接口
│   │   ├── task.py          # 任务管理接口
│   │   ├── upload.py        # 文件上传接口
│   │   └── lora.py          # LoRA模型接口
│   └── app.py               # Flask应用入口
├── config/                  # 配置文件
│   ├── wan/                 # 模型配置
│   ├── wan_fp8/             # FP8模型配置
│   └── config.py            # 应用配置
├── utils/                   # 工具函数
│   ├── logger.py            # 日志工具
│   ├── lora_utils.py        # LoRA模型工具
│   ├── model_scheduler.py   # 模型调度器
│   ├── rabbitmq_client.py   # RabbitMQ客户端
│   ├── redis_client.py      # Redis客户端
│   ├── task_manager.py      # 任务管理器
│   ├── task_worker.py       # 任务工作器
│   └── wan.py               # 模型调用工具
├── middlewares/             # 中间件
│   └── auth.py              # 认证中间件
├── LightX2V/                # LightX2V模型目录
├── web_code/                # 前端代码
├── supervisor/              # Supervisor配置
├── api.py                   # API服务启动脚本
├── start_worker.py          # 任务消费者启动脚本
├── requirements.api.txt     # API服务依赖
├── requirements.worker.txt  # 任务执行器依赖
├── requirements.fp8.txt     # FP8模型依赖
├── .env.example             # 环境变量示例
├── docker-compose.yml       # Docker Compose配置
├── Dockerfile_api           # API服务Dockerfile
├── Dockerfile_worker        # 任务执行器Dockerfile
└── README.md                # 项目说明
```

## API接口文档

启动服务后，可通过以下地址访问Swagger UI文档：

```
http://localhost:5001/api/docs
```

### 主要接口

- **认证接口**：登录获取JWT令牌
- **图像生成接口**：text2img, img2img
- **视频生成接口**：text2video, img2video
- **任务管理接口**：获取任务列表、任务详情
- **文件上传接口**：上传图像文件
- **LoRA模型接口**：管理LoRA模型
- **健康检查接口**：检查服务状态

### 接口示例

#### 文本到图像生成

```bash
POST /api/image/text2img
Content-Type: application/json
Authorization: Bearer <token>

{
  "prompt": "一只可爱的小猫在草地上玩耍",
  "negative_prompt": "模糊, 低分辨率",
  "steps": 9,
  "width": 544,
  "height": 544,
  "guidance_scale": 7.5
}
```

#### 文本到视频生成

```bash
POST /api/video/text2video
Content-Type: application/json
Authorization: Bearer <token>

{
  "prompt": "一只可爱的小猫在草地上玩耍",
  "negative_prompt": "模糊, 低分辨率",
  "steps": 4,
  "width": 544,
  "height": 960,
  "num_frames": 81
}
```

## 前端界面

项目内置了Vue前端界面，提供可视化的操作体验。需要提前编译前端网页，启动服务后，可通过以下地址访问：

```
http://localhost:5001
```
`注意`：默认的登录密码是`123456`，可以在配置文件.env里面修改

### 前端编译
```bash
cd web_code
npm install
npm run build
```

前端界面功能：
- 用户登录
- 图像生成（文生图、图生图）
- 视频生成（文生视频、图生视频）
- 任务管理和结果查看

### 快速部署平台

推荐在以下平台使用预配置的镜像直接部署，无需手动配置环境和下载模型：

- **AutoDL**：提供预配置的镜像
- **优云智算**：https://www.compshare.cn/images/UcHFPXcyOzKl?referral_code=GuXDHTANcHKEjlz2IlczOy

## 常见问题

### Q: 安装依赖时出现错误怎么办？
A: 请确保使用了正确的Python版本（3.11+），并已激活虚拟环境。如果是GPU相关错误，请检查CUDA版本是否与PyTorch版本兼容。

### Q: 启动服务时提示Redis或RabbitMQ连接失败？
A: 请确保Redis和RabbitMQ服务已正确启动，并且.env文件中的配置参数与实际服务配置一致。

### Q: 任务执行失败怎么办？
A: 请查看日志文件，检查错误信息。常见原因包括：
   - 模型文件缺失
   - GPU内存不足
   - 输入参数错误
   - 网络连接问题

### Q: 如何提高生成速度？
A: 可以尝试以下方法：
   - 使用FP8模型
   - 减少推理步数
   - 降低生成分辨率
   - 确保安装了Flash Attention

## 技术栈

- **后端框架**：Flask, Flask-RESTX
- **前端框架**：Vue 3, Vite
- **模型**：LightX2V, PyTorch
- **队列系统**：Redis, RabbitMQ
- **认证**：JWT
- **部署**：Docker, Docker Compose, Supervisor
- **加速技术**：Flash Attention

## 许可证

[MIT License](LICENSE)
