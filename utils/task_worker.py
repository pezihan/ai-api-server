import time
import os
import base64
import threading
import json
from utils.logger import logger
from utils.model_scheduler import model_scheduler
from utils.task_manager import task_manager
from utils.rabbitmq_client import rabbitmq_client
from config.config import config
from utils.lora_utils import get_lora_configs
from PIL import Image
class TaskWorker:
    """任务工作器，负责处理生成任务"""

    def __init__(self):
        self.is_running = False
        self.consumer_thread = None
        self.task_lock = threading.Lock()  # 用于确保任务顺序执行的锁
        self.message_queue = []  # 消息队列，用于存储待处理的消息
        self.message_queue_lock = threading.Lock()  # 消息队列锁
        self.worker_thread = None  # 工作线程
        self.worker_event = threading.Event()  # 工作线程事件，用于通知有新消息
    
    def _get_lora_configs(self, task_type, loras):
        """
        根据任务类型和lora对象获取对应的lora配置
        
        Args:
            task_type: str, 任务类型
            loras: list, lora对象列表，每个对象包含name和strength
            
        Returns:
            list: lora配置列表
        """
        return get_lora_configs(task_type, loras)
    
    def start(self):
        """启动任务工作器"""
        self.is_running = True
        
        # 启动工作线程
        self.worker_thread = threading.Thread(target=self._worker_thread)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        # 定义消息回调函数
        def on_message_received(ch, method, properties, body):
            """处理接收到的消息"""
            try:
                task_id = body.decode('utf-8')

                logger.info(f"接收到任务: {task_id}")

                # 获取任务信息
                task_info = task_manager.get_task(task_id)
                if not task_info:
                    logger.warning(f"任务不存在: {task_id}")
                    # 确认消息，即使任务不存在也需要ack
                    try:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        logger.info(f"任务不存在，已确认消息: {task_id}")
                    except Exception as ack_error:
                        logger.error(f"执行ack操作失败: {ack_error}")
                    return

                # 更新任务状态为处理中
                task_manager.update_task_status(task_id, 'processing')
                
                # 记录渲染开始时间
                render_start_time = time.time()
                task_manager.update_task_render_time(task_id, 'start', render_start_time)

                # 将消息添加到队列，由工作线程处理
                with self.message_queue_lock:
                    self.message_queue.append((ch, method, task_id, task_info))
                # 通知工作线程有新消息
                self.worker_event.set()

            except Exception as e:
                logger.error(f"处理消息时发生异常: {e}")
                # 在主线程中拒绝消息
                try:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    logger.info(f"消息拒绝成功: {task_id}")
                except Exception as nack_error:
                    logger.error(f"执行nack操作失败: {nack_error}")
        
        # 使用RabbitMQ的消息监听机制，添加异常处理
        try:
            rabbitmq_client.consume_messages(
                queue_name='ai_task_queue',
                callback=on_message_received,
                durable=True
            )
        except Exception as e:
            logger.error(f"消息消费过程中发生异常: {e}")
            # 当连接关闭或发生其他异常时，尝试重新启动消费
            if self.is_running:
                logger.info("尝试重新启动消息消费...")
                time.sleep(5)  # 等待5秒后重试
                self.start()  # 递归调用start方法重新启动消费
    
    def _worker_thread(self):
        """工作线程，负责处理消息队列中的任务"""
        logger.info("工作线程已启动")
        while self.is_running:
            # 等待新消息
            self.worker_event.wait()
            
            # 重置事件
            self.worker_event.clear()
            
            # 处理消息队列中的所有消息
            while self.is_running:
                # 获取消息
                with self.message_queue_lock:
                    if not self.message_queue:
                        break
                    ch, method, task_id, task_info = self.message_queue.pop(0)
                
                # 使用锁确保任务顺序执行
                with self.task_lock:
                    try:
                        # 执行任务
                        self._process_task(task_id, task_info)

                        # 任务处理完成，记录日志
                        logger.info(f"任务处理完成: {task_id}")
                        
                        # 任务完成后确认消息
                        try:
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            logger.info(f"消息确认成功: {task_id}")
                        except Exception as ack_error:
                            logger.error(f"执行ack操作失败: {ack_error}")
                    except Exception as e:
                        logger.error(f"处理任务时发生异常: {e}")
                        
                        # 任务失败时拒绝消息
                        try:
                            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                            logger.info(f"消息拒绝成功: {task_id}")
                        except Exception as nack_error:
                            logger.error(f"执行nack操作失败: {nack_error}")
    
    def stop(self):
        """停止任务工作器"""
        self.is_running = False
        # 通知工作线程停止
        self.worker_event.set()
        logger.info("任务工作器停止")
        # 停止消息消费
        from utils.rabbitmq_client import rabbitmq_client
        rabbitmq_client.stop_consuming()
    
    def _process_task(self, task_id, task_info):
        """
        处理任务
        
        Args:
            task_id: str, 任务ID
            task_info: dict, 任务信息
        """
        try:
            task_type = task_info['task_type']
            task_params = task_info['params']
            
            logger.info(f"开始处理任务: {task_id}, 类型: {task_type}")
            
            # 根据任务类型执行相应的处理
            if task_type in ['text2img', 'img2img']:
                result = self._process_image_task(task_type, task_params)
            elif task_type in ['text2video', 'img2video']:
                result = self._process_video_task(task_type, task_params)
            else:
                raise ValueError(f"不支持的任务类型: {task_type}")
            
            # 记录渲染结束时间
            render_end_time = time.time()
            task_manager.update_task_render_time(task_id, 'end', render_end_time)
            
            # 更新任务状态为完成
            task_manager.update_task_status(task_id, 'completed', result)
            logger.info(f"任务处理完成: {task_id}")

        except Exception as e:
            logger.error(f"处理任务 {task_id} 失败: {e}")
            
            # 即使任务失败，也记录渲染结束时间
            render_end_time = time.time()
            task_manager.update_task_render_time(task_id, 'end', render_end_time)
    
            # 更新任务状态为失败
            task_manager.update_task_status(task_id, 'failed', error=str(e))
            # 只有在检测到内存溢出错误时才卸载模型
            logger.warning(f"任务 {task_id} 执行失败，卸载当前模型")
            model_scheduler.unload_model()
                
                
    
    def _process_image_task(self, task_type, task_params):
        """
        处理图片生成任务
        
        Args:
            task_type: str, 任务类型 ('text2img' 或 'img2img')
            task_params: dict, 任务参数
            
        Returns:
            dict: 处理结果
        """
        import torch
        # 创建输出目录
        output_dir = os.path.join(config.FILE_SAVE_DIR, "ai-api-images")
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载qwen模型
        pipe = model_scheduler.load_model(task_type=task_type)
        
        prompt = task_params.get('prompt')
        negative_prompt = task_params.get('negative_prompt', '')
        seed = task_params.get('seed')
        steps = task_params.get('steps', 9)
        guidance_scale = task_params.get('guidance_scale', 5.0)
        width = task_params.get('width', 512)
        height = task_params.get('height', 512)
        loras = task_params.get('loras', [])
        
        # 处理LoRA配置
        lora_configs = self._get_lora_configs(task_type, loras)    

        # 设置随机生成器
        generator = torch.Generator(device="cuda").manual_seed(seed) if seed is not None else None
        
        if task_type == 'text2img':
            # 文生图任务
            # 执行生成
            output = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=guidance_scale,
                generator=generator,
                lora_configs=lora_configs
            )
            
        elif task_type == 'img2img':
            # 图生图任务
            image_path = task_params.get('image_path')
            
            # 验证文件路径存在
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            # 加载图片
            image = Image.open(image_path).convert("RGB")
            
            # 执行生成
            output = pipe(
                image=image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=steps,
                generator=generator,
                true_cfg_scale=4.0,
                guidance_scale=guidance_scale,
                num_images_per_prompt=1,
                width=width,
                height=height,
                lora_configs=lora_configs
            )
        
        # 获取生成的图片
        generated_image = output.images[0]
        
        # 生成唯一的输出文件名并保存
        timestamp = int(time.time())
        random_suffix = base64.urlsafe_b64encode(os.urandom(4)).decode('utf-8')
        output_filename = f"{task_type}_{timestamp}_{random_suffix}.png"
        output_path = os.path.join(output_dir, output_filename)
        
        generated_image.save(output_path, format="PNG")
        
        return {
            'image_path': output_path,
            'task_type': task_type
        }
    
    def _process_video_task(self, task_type, task_params):
        """
        处理视频生成任务
        
        Args:
            task_type: str, 任务类型 ('text2video' 或 'img2video')
            task_params: dict, 任务参数
            
        Returns:
            dict: 处理结果
        """
        import cv2

        prompt = task_params.get('prompt')
        negative_prompt = task_params.get('negative_prompt', '')
        seed = task_params.get('seed')
        steps = task_params.get('steps', 4)
        width = task_params.get('width', 544)
        height = task_params.get('height', 960)
        num_frames = task_params.get('num_frames', 81)
        loras = task_params.get('loras', [])
        
        # 处理LoRA配置
        lora_configs = self._get_lora_configs(task_type, loras)
        # 加载wan模型
        pipe = model_scheduler.load_model(task_type=task_type, lora_configs=lora_configs)
 
        # 生成唯一的输出路径
        output_dir = os.path.join(config.FILE_SAVE_DIR, "ai-api-videos")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{time.time()}_{seed}.mp4")
        
        if task_type == 'text2video':
            # 文生视频
            pipe(
                seed=seed,
                prompt=prompt,
                negative_prompt=negative_prompt,
                save_result_path=output_path,
                target_width=width,
                target_height=height,
                target_video_length=num_frames,
                infer_steps=steps
            )
        elif task_type == 'img2video':
            # 图生视频
            image_path = task_params.get('image_path')
            
            # 验证文件路径存在
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            pipe(
                seed=seed,
                image_path=image_path,
                prompt=prompt,
                negative_prompt=negative_prompt,
                save_result_path=output_path,
                target_width=width,
                target_height=height,
                target_video_length=num_frames,
                infer_steps=steps
            )
        
        # 生成视频封面（截取第一帧）
        cover_path = os.path.splitext(output_path)[0] + "_cover.jpg"
        cap = cv2.VideoCapture(output_path)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                # 保存封面图片
                cv2.imwrite(cover_path, frame)
                logger.info(f"视频封面生成成功: {cover_path}")
            cap.release()
        else:
            logger.warning(f"无法打开视频文件: {output_path}")
            cover_path = None

        return {
            'video_path': output_path,
            'cover_path': cover_path,
            'task_type': task_type
        }

# 创建全局任务工作器实例
task_worker = TaskWorker()