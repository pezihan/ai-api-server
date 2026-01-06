#!/bin/bash
set -e

repo_name="ai-server-worker"
image_tag="${repo_name}"

# 检查必要的文件
echo "=== 检查必要的文件 ==="
if [ ! -f "Dockerfile_worker" ]; then
    echo "错误: Dockerfile_worker 不存在"
    exit 1
fi

if [ ! -f "requirements.worker.txt" ]; then
    echo "错误: requirements.worker.txt 不存在"
    exit 1
fi

# 构建 Docker 镜像
echo "=== 开始构建 Docker 镜像 ==="
docker buildx --builder default build -f Dockerfile_worker -t ${image_tag}:update .

# 停止并删除旧容器（如果存在）
if [ "$(docker ps -q -f name=${image_tag})" ]; then
    echo "停止并删除旧容器..."
    docker stop ${image_tag}
    docker rm ${image_tag}
fi

# 更新镜像标签
echo "更新镜像标签..."
docker rmi -f ${image_tag}:latest 2>/dev/null || true
docker tag ${image_tag}:update ${image_tag}:latest
docker rmi ${image_tag}:update

# 运行新容器
echo "=== 启动新容器 ==="
docker run --restart=always \
 --name ${image_tag} \
 --gpus all \
 -v /home/ubuntu/tmp:/tmp \
 -v /home/ubuntu/models:/models \
 -e HF_ENDPOINT=https://hf-mirror.com \
 -d ${image_tag}:latest

# 验证部署状态
echo "=== 验证部署状态 ==="
sleep 2  # 等待容器启动
docker ps -a | grep ${image_tag}

if [ "$(docker ps -q -f name=${image_tag})" ]; then
    echo "=== 部署成功！Worker 服务已启动 ==="
else
    echo "=== 部署失败！Worker 服务未启动 ==="
    docker logs ${image_tag} 2>&1 | head -20
    exit 1
fi