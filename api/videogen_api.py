import os
import requests
import time
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("LUMA_API_KEY")
BASE_URL = "https://api.deerapi.com/dream-machine/v1"

def generate_video(prompt):
    """发送视频生成请求"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "loop": True
    }
    
    response = requests.post(
        f"{BASE_URL}/generations",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 201:
        return response.json()["id"]
    else:
        raise Exception(f"视频生成请求失败: {response.text}")

def check_generation_status(generation_id):
    """查询视频生成状态"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    response = requests.get(
        f"{BASE_URL}/generations/{generation_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"状态查询失败: {response.text}")

def wait_for_video_generation(prompt):
    """发起视频生成请求并等待完成"""
    # 发送生成请求
    generation_id = generate_video(prompt)
    print(f"视频生成任务已创建，ID: {generation_id}")
    
    # 循环查询状态
    while True:
        status_response = check_generation_status(generation_id)
        state = status_response.get("state")
        
        print(f"当前状态: {state}")
        
        if state == "completed":
            # 返回生成的视频URL
            return status_response["video"]["url"]
        elif state == "failed":
            raise Exception(f"视频生成失败: {status_response.get('failure_reason')}")
        
        # 等待30秒后再次查询
        time.sleep(30)

if __name__ == "__main__":
    try:
        prompt = "A tiger walking in snow"
        video_url = wait_for_video_generation(prompt)
        print(f"视频生成成功！URL: {video_url}")
    except Exception as e:
        print(f"错误: {str(e)}")