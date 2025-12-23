import requests
import base64
from io import BytesIO
from PIL import Image
import json

# 创建一个简单的测试图片
img = Image.new('RGB', (100, 100), color='red')
buffer = BytesIO()
img.save(buffer, format="PNG")
image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

# 登录获取的token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjY1MDM5NzUuMzQ4ODMyLCJpYXQiOjE3NjY1MDAzNzUuMzQ4ODM1fQ.5zfwiMmqsE2kFprG8zt7_jNOdwJh-IFS0nG3TasXsxk"

# 测试img2img接口
url = "http://localhost:5001/image/img2img"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "prompt": "a beautiful landscape",
    "negative_prompt": "ugly, bad quality",
    "image": image_base64
}

print("发送img2img请求...")
try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
except Exception as e:
    print(f"请求失败: {e}")
