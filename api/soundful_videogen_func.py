import time
import os
import requests
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from api.videogen_api_utils import generate_video, check_generation_status
from api.video2audio_func import video2audio

def download_video(url, save_path, max_retries=3, timeout=30):
    """
    从URL下载视频到指定路径
    
    Args:
        url (str): 视频下载链接
        save_path (str): 保存路径
        max_retries (int): 最大重试次数
        timeout (int): 超时时间(秒)
    
    Returns:
        str: 下载文件的完整路径
    """
    # 创建保存目录
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # 配置重试策略
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        # 发送请求并获取文件大小
        response = session.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        file_size = int(response.headers.get('content-length', 0))
        
        # 使用tqdm显示下载进度
        with open(save_path, 'wb') as f, tqdm(
            desc=os.path.basename(save_path),
            total=file_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                pbar.update(size)
        
        return save_path
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"下载视频失败: {str(e)}")
    finally:
        session.close()

def main(prompt, aspect_ratio="16:9", image_url=None, user_id="00000000000000000000000000000000"):
    """发起视频生成请求并等待完成"""
    # 发送生成请求
    generation_id = generate_video(prompt, aspect_ratio=aspect_ratio, loop=True, image_url=image_url)
    print(f"视频生成任务已创建，ID: {generation_id}")
    
    # 循环查询状态
    while True:
        status_response = check_generation_status(generation_id)
        state = status_response.get("state")
        
        print(f"任务ID: {generation_id} 当前状态: {state}")
        
        if state == "completed":
            url = status_response["video"]["url"]
            
            # 下载视频到本地
            save_dir = "/workspace/tmp" if user_id is None else f"/workspace/tmp/{user_id}"
            video_name = f"video_{generation_id}.mp4"
            video_path = os.path.join(save_dir, video_name)
            
            try:
                download_video(url, video_path)
                print(f"视频已下载到: {video_path}")

                # 生成有声视频
                soundful_video_path = video2audio(
                    video_path=video_path,
                    user_id=user_id,
                    task_id=generation_id
                )
                return soundful_video_path
            except Exception as e:
                print(f"失败: {str(e)}")
                return url
        elif state == "failed":
            raise Exception(f"视频生成失败: {status_response.get('failure_reason')}")
        
        # 等待30秒后再次查询
        time.sleep(30)


if __name__ == "__main__":
    soundful_video_path = video2audio(
        video_path="/workspace/tmp/video_ff399c40-f9ee-46b6-8043-b51ddee54e73.mp4",
        user_id="00000000000000000000000000000012",
        task_id="ff399c40-f9ee-46b6-8043-b51ddee54e73"
    )
    exit()
    try:
        prompt = "A tiger walking in snow"
        result = main(prompt)
        print(f"处理完成！结果: {result}")
    except Exception as e:
        print(f"错误: {str(e)}")