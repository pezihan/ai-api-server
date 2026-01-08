# AI API Server

一个基于Flask的AI API服务，提供图像和视频生成功能，支持任务队列和文件管理。

## 功能特性

- 🖼️ 图像生成：支持文本到图像（text2img）和图像到图像（img2img）生成
- 🎬 视频生成：支持文本到视频（text2video）和图像到视频（img2video）生成
- 📂 文件管理：提供静态文件访问服务，支持多级目录结构
- 📋 任务队列：使用Redis存储任务信息，RabbitMQ作为任务队列
- 🔐 身份认证：基于JWT的身份认证机制
- 🐳 Docker支持：提供Docker部署配置

## 快速开始

### 环境要求

- Python 3.11+
- Conda（推荐用于创建虚拟环境）
- GPU支持（用于图像和视频生成）

### 1. 创建虚拟环境

```bash
conda create -n ai-server python=3.11 -y
conda activate ai-server
```

### 2. 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt
```

### 3. 安装LightX2V依赖

```bash
cd LightX2V
pip install -v -e .
```

### 安装推理加速
```
pip install flash-attn --no-build-isolation

# 可以从以下链接下载预编译的whl文件
https://github.com/Dao-AILab/flash-attention/releases/tag/v2.8.3

# python3.12 + torch2.8.0 + cuda12.1 通过测试
flash_attn-2.8.3+cu12torch2.8cxx11abiTRUE-cp312-cp312-linux_x86_64.whl
```

# 安装其他依赖
如果使用fb8模型需要安装
```bash
pip install -r requirements_fb8.txt

git clone https://github.com/KONAKONA666/q8_kernels
cd q8_kernels 
git submodule init
git submodule update
python setup.py install
pip install --no-build-isolation .
```

### 4. 配置环境变量

复制环境变量示例文件并根据需要修改：

```bash
cp .env.example .env
```

编辑`.env`文件，配置以下关键参数：

```bash
# 服务配置
SECRET_KEY=your_secret_key
DEBUG=False
HOST=0.0.0.0
PORT=5001

# 登录密码
LOGIN_PASSWORD=your_login_password

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# RabbitMQ配置
RABBITMQ_HOST=127.0.0.1
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=admin
RABBITMQ_PASSWORD=your_rabbitmq_password
RABBITMQ_VIRTUAL_HOST=/
```

### 5. 启动Redis和RabbitMQ

#### 方式一：本地安装（推荐用于开发）

请参考各自官方文档安装Redis和RabbitMQ。

#### 方式二：Docker部署（推荐用于生产）

```bash
docker-compose up -d
```

详细配置请参考`docker-compose.yml`和`README_DOCKER.md`。

### 6. 启动服务

#### 6.1 启动API接口服务
复制`supervisor.worker.conf`、`supervisor.api.conf`到`/etc/supervisor/conf.d/`目录下
```bash
# 重新加载配置（新增/修改配置后必须执行）
sudo supervisorctl reload

# 启动你的进程（替换为配置中的program名，比如my_app）
sudo supervisorctl start ai-server-worker

# 查看所有进程状态
sudo supervisorctl status

# 重启进程
sudo supervisorctl restart ai-server-worker

# 停止进程
sudo supervisorctl stop ai-server-worker

# 实时查看日志（排错用）
sudo supervisorctl tail -f ai-server-worker  # 查看标准输出
sudo supervisorctl tail -f ai-server-worker stderr  # 查看错误日志
```


API服务将在`http://localhost:5001`启动，文档可通过`http://localhost:5001/api/docs`访问。

#### 6.2 启动任务队列消费者服务

```bash
python start_worker.py
```

任务消费者将开始处理队列中的任务。

## 项目结构

```
ai-api-server/
├── app/                     # Flask应用目录
│   ├── api/                 # API接口定义
│   │   ├── auth.py          # 认证接口
│   │   ├── image.py         # 图像生成接口
│   │   ├── video.py         # 视频生成接口
│   │   ├── task.py          # 任务管理接口
│   │   └── health.py        # 健康检查接口
│   └── app.py               # Flask应用入口
├── config/                  # 配置文件
│   └── config.py            # 应用配置
├── utils/                   # 工具函数
│   ├── task_manager.py      # 任务管理器
│   ├── task_worker.py       # 任务工作器
│   ├── redis_client.py      # Redis客户端
│   ├── rabbitmq_client.py   # RabbitMQ客户端
│   └── logger.py            # 日志工具
├── LightX2V/                # LightX2V模型目录
├── run.py                   # API服务启动脚本
├── start_worker.py          # 任务消费者启动脚本
├── requirements.txt         # 依赖列表
├── .env.example             # 环境变量示例
├── docker-compose.yml       # Docker Compose配置
└── README.md                # 项目说明
```

## API接口文档

启动服务后，可通过以下地址访问Swagger UI文档：

```
http://localhost:5001/api/docs
```

主要接口包括：

- **认证接口**：登录获取JWT令牌
- **图像生成接口**：text2img, img2img
- **视频生成接口**：text2video, img2video
- **任务管理接口**：获取任务列表、任务详情
- **文件访问接口**：访问生成的图像和视频文件

## 常见问题

### Q: 安装依赖时出现错误怎么办？
A: 请确保使用了正确的Python版本（3.11+），并已激活虚拟环境。如果是GPU相关错误，请检查CUDA版本是否与PyTorch版本兼容。

### Q: 启动服务时提示Redis或RabbitMQ连接失败？
A: 请确保Redis和RabbitMQ服务已正确启动，并且.env文件中的配置参数与实际服务配置一致。

### Q: 任务执行失败怎么办？
A: 请查看日志文件，检查错误信息。常见原因包括模型文件缺失、GPU内存不足等。

### Q: 如何访问生成的文件？
A: 生成的文件会保存在`FILE_SAVE_DIR`配置的目录中，可以通过`/temp/`开头的URL访问（例如：`http://localhost:5001/temp/ai-api-images/xxx.png`）。

## 技术栈

- **框架**：Flask, Flask-RESTX
- **模型**：LightX2V, PyTorch
- **队列**：Redis, RabbitMQ
- **认证**：JWT
- **部署**：Docker, Docker Compose

## 许可证

[MIT License](LICENSE)
