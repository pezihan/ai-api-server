cp supervisor.worker.conf /etc/supervisor/conf.d/
cp supervisor.api.conf /etc/supervisor/conf.d/
cp supervisor.redis.conf /etc/supervisor/conf.d/
cp supervisor.rabbitmq.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl status