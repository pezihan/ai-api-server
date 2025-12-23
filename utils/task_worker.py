import time
import json
import os
import base64
from io import BytesIO
from PIL import Image
import torch
from utils.logger import logger
from utils.model_scheduler import model_scheduler
from utils.task_manager import task_manager
from utils.rabbitmq_client import rabbitmq_client

class TaskWorker:
    """任务工作器，负责处理生成任务"""
    
    def __init__(self):
        self.is_running = False
        self.consumer_thread = None
    
    def start(self):
        """启动任务工作器"""
        self.is_running = True
        
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
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                # 更新任务状态为处理中
                task_manager.update_task_status(task_id, 'processing')
                
                # 执行任务
                self._process_task(task_id, task_info)
                
                # 任务处理完成，确认消息
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"任务处理完成并确认: {task_id}")
                
            except Exception as e:
                logger.error(f"处理任务时发生异常: {e}")
                # 任务处理失败，重新入队
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        # 使用RabbitMQ的消息监听机制
        rabbitmq_client.consume_messages(
            queue_name='ai_task_queue',
            callback=on_message_received,
            durable=True
        )
    
    def stop(self):
        """停止任务工作器"""
        self.is_running = False
        logger.info("任务工作器停止")
    
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
            
            # 更新任务状态为完成
            task_manager.update_task_status(task_id, 'completed', result)
            logger.info(f"任务处理完成: {task_id}")
            
        except Exception as e:
            logger.error(f"处理任务 {task_id} 失败: {e}")
            # 更新任务状态为失败
            task_manager.update_task_status(task_id, 'failed', error=str(e))
    
    def _process_image_task(self, task_type, task_params):
        """
        处理图片生成任务
        
        Args:
            task_type: str, 任务类型 ('text2img' 或 'img2img')
            task_params: dict, 任务参数
            
        Returns:
            dict: 处理结果
        """
        # 加载qwen模型
        pipe = model_scheduler.load_model('qwen')
        
        prompt = task_params.get('prompt')
        negative_prompt = task_params.get('negative_prompt', '')
        seed = task_params.get('seed')
        steps = task_params.get('steps', 50)
        
        # 设置随机生成器
        generator = torch.Generator(device="cuda").manual_seed(seed) if seed is not None else None
        
        if task_type == 'text2img':
            # 文生图任务
            width = task_params.get('width', 512)
            height = task_params.get('height', 512)
            
            # 执行生成
            output = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=steps,
                generator=generator
            )
            
        elif task_type == 'img2img':
            # 图生图任务
            image_base64 = task_params.get('image')
            
            # 解码base64图片
            image_data = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_data)).convert("RGB")
            
            # 执行生成
            output = pipe(
                image=image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=steps,
                generator=generator
            )
        
        # 获取生成的图片
        generated_image = output.images[0]
        
        # 将图片转换为base64编码
        buffer = BytesIO()
        generated_image.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return {
            'image': image_base64,
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
        prompt = task_params.get('prompt')
        negative_prompt = task_params.get('negative_prompt', '')
        seed = task_params.get('seed')
        steps = task_params.get('steps', 50)
        width = task_params.get('width', 480)
        height = task_params.get('height', 832)
        num_frames = task_params.get('num_frames', 81)
        
        # 根据任务类型加载相应的wan模型
        if task_type == 'text2video':
            pipe = model_scheduler.load_model('wan', task='t2v')
        elif task_type == 'img2video':
            pipe = model_scheduler.load_model('wan', task='i2v')
        
        # 创建生成器
        pipe.create_generator(
            attn_mode="sage_attn2",
            infer_steps=steps,
            height=height,
            width=width,
            num_frames=num_frames,
            guidance_scale=5.0,
            sample_shift=5.0,
        )
        
        # 生成唯一的输出路径
        output_dir = "/tmp/ai-api-videos"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{time.time()}_{seed}.mp4")
        
        if task_type == 'text2video':
            # 文生视频
            pipe.generate(
                seed=seed,
                prompt=prompt,
                negative_prompt=negative_prompt,
                save_result_path=output_path,
            )
        elif task_type == 'img2video':
            # 图生视频
            image_base64 = task_params.get('image')
            
            # 解码base64图片并保存到临时文件
            image_data = base64.b64decode(image_base64)
            temp_image_path = os.path.join(output_dir, f"temp_{time.time()}.png")
            with open(temp_image_path, 'wb') as f:
                f.write(image_data)
            
            try:
                pipe.generate(
                    seed=seed,
                    image_path=temp_image_path,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    save_result_path=output_path,
                )
            finally:
                # 删除临时图片
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
        
        # 将视频文件转换为base64编码
        with open(output_path, 'rb') as f:
            video_data = f.read()
        video_base64 = base64.b64encode(video_data).decode("utf-8")
        
        # 删除临时视频文件
        if os.path.exists(output_path):
            os.remove(output_path)
        
        return {
            'video': video_base64,
            'task_type': task_type
        }

# 创建全局任务工作器实例
task_worker = TaskWorker()