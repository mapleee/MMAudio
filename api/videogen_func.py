import time
from api.videogen_api_utils import generate_video, check_generation_status

def main(prompt, aspect_ratio="16:9", image_url=None):
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
            # 返回生成的视频URL
            return status_response["video"]["url"]
        elif state == "failed":
            raise Exception(f"视频生成失败: {status_response.get('failure_reason')}")
        
        # 等待30秒后再次查询
        time.sleep(30)


if __name__ == "__main__":
    try:
        prompt = "A tiger walking in snow"
        video_url = main(prompt)
        print(f"视频生成成功！URL: {video_url}")
    except Exception as e:
        print(f"错误: {str(e)}")