from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from api.videogen_func import main
import asyncio
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Video Generation API",
    description="API for generating videos from text prompts",
    version="1.0.0"
)

class VideoGenRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for video generation")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio of the video (e.g., '16:9', '1:1')")
    loop: bool = Field(default=True, description="Whether the video should loop")
    image_url: Optional[str] = Field(default=None, description="Optional reference image URL")

class VideoGenResponse(BaseModel):
    status: str
    message: str
    video_url: Optional[str] = None
    generation_id: Optional[str] = None

@app.post("/api/v1/generate-video", response_model=VideoGenResponse)
async def generate_video(request: VideoGenRequest):
    try:
        # 将同步操作转换为异步操作
        video_url = await asyncio.to_thread(
            main,
            request.prompt,
            aspect_ratio=request.aspect_ratio,
            loop=request.loop,
            image_url=request.image_url
        )
        
        return VideoGenResponse(
            status="success",
            message="Video generated successfully",
            video_url=video_url
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
