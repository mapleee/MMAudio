import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("LUMA_API_KEY")
BASE_URL = "https://api.deerapi.com/dream-machine/v1"

def generate_video(prompt, aspect_ratio="16:9", loop=True, image_url=None):
    """发送视频生成请求"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    if image_url is not None:
        keyframes = {
            "frames0": {
                "type": "image",
                "url": image_url
            }
        }
    else:
        keyframes = None

    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "loop": loop,
        "keyframes":keyframes
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
