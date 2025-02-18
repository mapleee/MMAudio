from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from api.videogen_func import main as videogen_main
from api.soundful_videogen_func import main as soundful_videogen_main
import asyncio
from fastapi.responses import JSONResponse
import redis
import json
import uuid
from datetime import datetime

app = FastAPI(
    title="Video Generation API",
    description="API for generating videos from text prompts",
    version="1.0.0"
)

# Redis 配置
redis_client = redis.Redis(host='localhost', port=6379, db=0)
QUEUE_KEY = "video_generation_queue"
MAX_CONCURRENT_TASKS = 5
TASK_PREFIX = "task:"

class VideoGenRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for video generation")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio of the video (e.g., '16:9', '1:1')")
    image_url: Optional[str] = Field(default=None, description="Optional reference image URL")

class SoundfulVideoGenRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for video generation")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio of the video (e.g., '16:9', '1:1')")
    image_url: Optional[str] = Field(default=None, description="Optional reference image URL")
    user_id: Optional[str] = Field(default="00000000000000000000000000000000", description="User ID")

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None

class VideoGenResponse(BaseModel):
    status: str
    message: str
    task_id: str
    video_url: Optional[str] = None

async def process_video_generation_queue():
    while True:
        # 检查当前正在处理的任务数
        processing_tasks = len([k for k in redis_client.keys(f"{TASK_PREFIX}*")
                              if json.loads(redis_client.get(k))["status"] == "processing"])
        
        if processing_tasks < MAX_CONCURRENT_TASKS:
            # 从队列中获取任务
            task_data = redis_client.lpop(QUEUE_KEY)
            if task_data:
                task_data = json.loads(task_data)
                task_id = task_data["task_id"]
                
                # 更新任务状态为处理中
                task_info = json.loads(redis_client.get(f"{TASK_PREFIX}{task_id}"))
                task_info["status"] = "processing"
                redis_client.set(f"{TASK_PREFIX}{task_id}", json.dumps(task_info))
                
                try:
                    if task_data["type"] == "normal":
                        video_url = await asyncio.to_thread(
                            videogen_main,
                            task_data["prompt"],
                            aspect_ratio=task_data["aspect_ratio"],
                            image_url=task_data.get("image_url")
                        )
                    else:  # soundful
                        video_url = await asyncio.to_thread(
                            soundful_videogen_main,
                            task_data["prompt"],
                            aspect_ratio=task_data["aspect_ratio"],
                            image_url=task_data.get("image_url"),
                            user_id=task_data.get("user_id")
                        )
                    
                    # 更新任务状态为完成
                    task_info.update({
                        "status": "completed",
                        "completed_at": datetime.now().isoformat(),
                        "result": {"video_url": video_url}
                    })
                except Exception as e:
                    # 更新任务状态为失败
                    task_info.update({
                        "status": "failed",
                        "completed_at": datetime.now().isoformat(),
                        "error": str(e)
                    })
                
                redis_client.set(f"{TASK_PREFIX}{task_id}", json.dumps(task_info))
        
        await asyncio.sleep(1)  # 避免过度轮询

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_video_generation_queue())

@app.post("/generate-video", response_model=VideoGenResponse)
async def generate_video(request: VideoGenRequest):
    task_id = str(uuid.uuid4())
    task_info = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "type": "normal"
    }
    
    # 存储任务信息
    redis_client.set(f"{TASK_PREFIX}{task_id}", json.dumps(task_info))
    
    # 将任务添加到队列
    task_data = {
        "task_id": task_id,
        "type": "normal",
        "prompt": request.prompt,
        "aspect_ratio": request.aspect_ratio,
        "image_url": request.image_url
    }
    redis_client.rpush(QUEUE_KEY, json.dumps(task_data))
    
    return VideoGenResponse(
        status="accepted",
        message="Task submitted successfully",
        task_id=task_id
    )

@app.post("/generate-soundful-video", response_model=VideoGenResponse)
async def generate_soundful_video(request: SoundfulVideoGenRequest):
    task_id = str(uuid.uuid4())
    task_info = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "type": "soundful"
    }
    
    # 存储任务信息
    redis_client.set(f"{TASK_PREFIX}{task_id}", json.dumps(task_info))
    
    # 将任务添加到队列
    task_data = {
        "task_id": task_id,
        "type": "soundful",
        "prompt": request.prompt,
        "aspect_ratio": request.aspect_ratio,
        "image_url": request.image_url,
        "user_id": request.user_id
    }
    redis_client.rpush(QUEUE_KEY, json.dumps(task_data))
    
    return VideoGenResponse(
        status="accepted",
        message="Task submitted successfully",
        task_id=task_id
    )

@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    task_info = redis_client.get(f"{TASK_PREFIX}{task_id}")
    if not task_info:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    return TaskStatus(**json.loads(task_info))

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7870)
