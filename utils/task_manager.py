import json
import uuid
import time
from utils.redis_client import redis_client
from utils.rabbitmq_client import rabbitmq_client
from utils.logger import logger

class TaskManager:
    """任务管理器，使用Redis存储任务信息，使用RabbitMQ作为任务队列"""
    
    def __init__(self):
        self.redis = redis_client
        self.rabbitmq = rabbitmq_client
        self.task_queue_name = "ai_task_queue"
        self.task_info_key_prefix = "ai_task:info:"
    
    def create_task(self, task_type, task_params):
        """
        创建新任务
        
        Args:
            task_type: str, 任务类型 ('text2img', 'img2img', 'text2video', 'img2video')
            task_params: dict, 任务参数
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        task_info = {
            'task_id': task_id,
            'task_type': task_type,
            'params': task_params,
            'status': 'pending',  # pending, processing, completed, failed
            'created_at': timestamp,
            'updated_at': timestamp,
            'result': None,
            'error': None
        }
        
        # 存储任务信息到Redis
        task_key = f"{self.task_info_key_prefix}{task_id}"
        self.redis.set(task_key, json.dumps(task_info))
        
        # 将任务ID加入RabbitMQ队列
        self.rabbitmq.publish_message(self.task_queue_name, task_id, durable=True)
        
        logger.info(f"创建任务成功: {task_id}, 类型: {task_type}")
        return task_id
    
    def get_task(self, task_id):
        """
        获取任务信息
        
        Args:
            task_id: str, 任务ID
            
        Returns:
            dict: 任务信息
        """
        task_key = f"{self.task_info_key_prefix}{task_id}"
        task_info_str = self.redis.get(task_key)
        if task_info_str:
            return json.loads(task_info_str)
        return None
    
    def update_task_status(self, task_id, status, result=None, error=None):
        """
        更新任务状态
        
        Args:
            task_id: str, 任务ID
            status: str, 任务状态
            result: any, 任务结果
            error: str, 错误信息
        """
        task_info = self.get_task(task_id)
        if not task_info:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        task_info['status'] = status
        task_info['updated_at'] = int(time.time())
        
        if result is not None:
            task_info['result'] = result
        if error is not None:
            task_info['error'] = error
        
        task_key = f"{self.task_info_key_prefix}{task_id}"
        self.redis.set(task_key, json.dumps(task_info))
        
        logger.info(f"更新任务状态: {task_id}, 状态: {status}")
        return True
    
    def get_task_list(self, page=1, page_size=10, status=None):
        """
        获取任务列表
        
        Args:
            page: int, 页码
            page_size: int, 每页数量
            status: str, 任务状态过滤（可选）
            
        Returns:
            dict: 任务列表和总数
        """
        # 获取所有任务键
        all_task_keys = self.redis.keys(f"{self.task_info_key_prefix}*")
        
        tasks = []
        for key in all_task_keys:
            task_info_str = self.redis.get(key)
            if task_info_str:
                task_info = json.loads(task_info_str)
                # 根据状态过滤
                if status and task_info['status'] != status:
                    continue
                tasks.append(task_info)
        
        # 按创建时间倒序排序
        tasks.sort(key=lambda x: x['created_at'], reverse=True)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_tasks = tasks[start:end]
        
        return {
            'total': len(tasks),
            'page': page,
            'page_size': page_size,
            'tasks': paginated_tasks
        }
    

    
    def requeue_task(self, task_id):
        """
        将任务重新加入RabbitMQ队列
        
        Args:
            task_id: str, 任务ID
        """
        self.rabbitmq.publish_message(self.task_queue_name, task_id, durable=True)
        logger.info(f"任务重新加入RabbitMQ队列: {task_id}")
    
    def delete_task(self, task_id):
        """
        删除任务
        
        Args:
            task_id: str, 任务ID
        """
        task_key = f"{self.task_info_key_prefix}{task_id}"
        self.redis.delete(task_key)
        logger.info(f"任务删除成功: {task_id}")

# 创建全局任务管理器实例
task_manager = TaskManager()