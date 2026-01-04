# Docker部署Redis和RabbitMQ配置说明

## 配置文件说明

本项目使用Docker Compose来部署Redis和RabbitMQ服务，配置文件为`docker-compose.yml`。

### Redis配置
- 镜像：redis:7.0-alpine（轻量级Alpine版本）
- 端口映射：6379:6379
- 密码：123456（可通过.env文件修改）
- 数据持久化：启用appendonly模式，数据保存在redis-data卷中

### RabbitMQ配置
- 镜像：rabbitmq:3.11-management-alpine（带管理界面的Alpine版本）
- 端口映射：5672:5672（AMQP端口），15672:15672（管理界面端口）
- 用户名：admin
- 密码：admin
- 虚拟主机：/
- 数据持久化：数据保存在rabbitmq-data卷中，日志保存在rabbitmq-log卷中

## 使用方法

### 启动服务

```bash
docker-compose up -d
```

该命令会在后台启动Redis和RabbitMQ服务。

### 查看服务状态

```bash
docker-compose ps
```

### 停止服务

```bash
docker-compose down
```

该命令会停止并移除容器，但不会删除数据卷。

### 停止服务并删除数据卷

```bash
docker-compose down -v
```

### 查看服务日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs redis
docker-compose logs rabbitmq
```

## 访问管理界面

### RabbitMQ管理界面

启动服务后，可以通过以下地址访问RabbitMQ管理界面：
- 地址：http://localhost:15672
- 用户名：admin
- 密码：admin

## 与应用集成

确保应用的.env文件中的Redis和RabbitMQ配置与docker-compose.yml中的配置一致：

```
# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=123456
REDIS_DB=0

# RabbitMQ配置
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=admin
RABBITMQ_PASSWORD=admin
RABBITMQ_VIRTUAL_HOST=/
```

注意：这里的REDIS_HOST和RABBITMQ_HOST应该使用容器名称（redis和rabbitmq），而不是localhost，因为容器之间需要通过Docker网络通信。
