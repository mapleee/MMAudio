from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Set
from api.video2audio_func import video2audio
import asyncio
from fastapi.responses import JSONResponse
import redis
import json
import uuid
from datetime import datetime
from asyncio import Queue, Task
from api.video_upload import router as video_router


app = FastAPI(
    title="Video to Audio API",
    description="API for generating audio from video",
    version="1.0.0"
)
app.include_router(video_router)

# Redis 配置
redis_client = redis.Redis(host='localhost', port=6379, db=0)
QUEUE_KEY = "video2audio_queue"
MAX_CONCURRENT_TASKS = 2
TASK_PREFIX = "v2a_task:"

# 添加全局变量来跟踪运行中的任务
running_tasks: Set[Task] = set()
task_queue: Queue = Queue()

# 任务状态常量
class TaskState:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Video2AudioRequest(BaseModel):
    video_path: str = Field(..., description="Path to the video file")
    user_id: str = Field(default="00000000000000000000000000000000", description="User ID")
    prompt: str = Field(default="", description="Prompt for the audio")
    negative_prompt: str = Field(default="music", description="Negative prompt for the audio")

class TaskStatus(BaseModel):
    task_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None

class Video2AudioResponse(BaseModel):
    status: str
    message: str
    task_id: str
    video_url: Optional[str] = None

async def process_single_task(task_data: dict):
    task_id = task_data["task_id"]
    
    try:
        # 更新任务状态为处理中
        task_info = {
            "task_id": task_id,
            "status": TaskState.PROCESSING,
            "created_at": task_data["created_at"],
            "updated_at": datetime.now().isoformat()
        }
        redis_client.set(f"{TASK_PREFIX}{task_id}", json.dumps(task_info))
        
        try:
            video_url = await asyncio.to_thread(
                video2audio,
                task_data["video_path"],
                task_data["user_id"],
                task_id,
                task_data["prompt"],
                task_data["negative_prompt"],
            )
            
            # 更新任务状态为完成
            task_info.update({
                "status": TaskState.COMPLETED,
                "completed_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "result": {"video_url": video_url}
            })
        except Exception as e:
            # 更新任务状态为失败
            task_info.update({
                "status": TaskState.FAILED,
                "completed_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "error": str(e)
            })
        
        # 使用事务来确保状态更新的原子性
        pipe = redis_client.pipeline()
        pipe.set(f"{TASK_PREFIX}{task_id}", json.dumps(task_info))
        pipe.execute()
        
    finally:
        current_task = asyncio.current_task()
        if current_task in running_tasks:
            running_tasks.remove(current_task)

async def process_video2audio_queue():
    while True:
        # 检查是否可以启动新任务
        while len(running_tasks) < MAX_CONCURRENT_TASKS:
            # 从Redis队列中获取任务
            task_data = redis_client.lpop(QUEUE_KEY)
            if not task_data:
                break  # 队列为空
                
            task_data = json.loads(task_data)
            # 创建新的任务并加入到运行集合中
            task = asyncio.create_task(process_single_task(task_data))
            running_tasks.add(task)
            
        # 等待一小段时间后继续检查
        await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    # 启动队列处理器
    asyncio.create_task(process_video2audio_queue())

@app.post("/video2audio", response_model=Video2AudioResponse)
async def convert_video_to_audio(request: Video2AudioRequest):
    task_id = str(uuid.uuid4())
    created_time = datetime.now().isoformat()
    
    task_info = {
        "task_id": task_id,
        "status": TaskState.PENDING,
        "created_at": created_time,
        "updated_at": created_time
    }
    
    # 使用事务来确保任务创建的原子性
    pipe = redis_client.pipeline()
    pipe.set(f"{TASK_PREFIX}{task_id}", json.dumps(task_info))
    
    # 将任务添加到队列
    task_data = {
        "task_id": task_id,
        "video_path": request.video_path,
        "user_id": request.user_id,
        "prompt": request.prompt,
        "negative_prompt": request.negative_prompt,
        "created_at": created_time
    }
    pipe.rpush(QUEUE_KEY, json.dumps(task_data))
    pipe.execute()
    
    return Video2AudioResponse(
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
    
    task_data = json.loads(task_info)
    return TaskStatus(**task_data)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7880)
