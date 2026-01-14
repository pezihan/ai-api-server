# 启动API接口服务
## 安装redis与rabbitmq
```bash
apt install redis-server -y
apt install rabbitmq-server -y
```

把api、worker、redis、rabbitmq的启动配置复制到supervisor的配置目录下，根据实际情况决定要不要把redis和rabbitmq的supervisor的配置文件复制到supervisor的配置目录下

```bash
sudo apt install -y supervisor
# 重新加载配置（新增/修改配置后必须执行）
sudo supervisorctl reload

# 启动你的进程（替换为配置中的program名，比如my_app）
sudo supervisorctl start ai_server_worker

# 查看所有进程状态
sudo supervisorctl status

# 重启进程
sudo supervisorctl restart ai_server_worker

# 停止进程
sudo supervisorctl stop ai_server_worker

# 实时查看日志（排错用）
sudo supervisorctl tail -f ai_server_worker  # 查看标准输出
sudo supervisorctl tail -f ai_server_worker stderr  # 查看错误日志
```

API服务将在`http://localhost:5001`启动，文档可通过`http://localhost:5001/api/docs`访问。
