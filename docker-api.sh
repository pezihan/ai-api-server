#!/bin/bash
set -e

repo_name="ai-server-api"
image_tag="${repo_name}"

# 编译前端网页
echo "=== 开始编译前端网页 ==="
cd web_code

# 检查 package.json 是否存在
if [ ! -f "package.json" ]; then
    echo "错误: package.json 不存在"
    exit 1
fi

# 安装依赖
echo "安装前端依赖..."
npm install

# 构建前端
echo "构建前端项目..."
npm run build

cd ..
echo "=== 前端网页编译完成 ==="

# 构建 Docker 镜像
echo "=== 开始构建 Docker 镜像 ==="
docker buildx --builder default build -f Dockerfile_api -t ${image_tag}:update .

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
 -v /home/ubuntu/tmp:/tmp \
 -p 5001:5001 \
 -d ${image_tag}:latest

echo "=== 部署完成 ==="
docker ps -a | grep ${image_tag}