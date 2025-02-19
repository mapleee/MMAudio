from fastapi import APIRouter, UploadFile, HTTPException, File
from fastapi.responses import JSONResponse
import os
from typing import List
import aiofiles
from datetime import datetime

router = APIRouter()

# 配置上传文件的保存路径
UPLOAD_DIR = "/workspace/tmp"
# 允许的视频文件类型
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
# 最大文件大小 (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024  


def validate_video_file(file: UploadFile) -> None:
    """验证上传的视频文件"""
    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。允许的文件类型: {', '.join(ALLOWED_EXTENSIONS)}"
        )

@router.post("/upload/video", response_class=JSONResponse)
async def upload_video(
    file: UploadFile,
    user_id: str
):
    """
    上传视频文件的端点
    """
    try:
        # 检查文件大小
        size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        chunks = []
        
        while chunk := await file.read(chunk_size):
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"文件太大。最大允许大小为 {MAX_FILE_SIZE/(1024*1024)}MB"
                )
            chunks.append(chunk)
            
        # 重置文件指针
        await file.seek(0)
            
        # 验证文件
        validate_video_file(file)
        
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file.filename)[1]
        new_filename = f"{timestamp}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, user_id, new_filename)
        os.makedirs(os.path.join(UPLOAD_DIR, user_id), exist_ok=True)
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as out_file:
            for chunk in chunks:
                await out_file.write(chunk)
        
        return JSONResponse(
            content={
                "message": "视频上传成功",
                "filename": new_filename,
                "path": file_path
            },
            status_code=200
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"上传失败: {str(e)}"
        )

@router.get("/videos", response_class=JSONResponse)
async def list_videos():
    """
    获取已上传视频列表的端点
    """
    try:
        videos = []
        for filename in os.listdir(UPLOAD_DIR):
            if os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS:
                file_path = os.path.join(UPLOAD_DIR, filename)
                videos.append({
                    "filename": filename,
                    "path": file_path,
                    "size": os.path.getsize(file_path)
                })
        
        return JSONResponse(
            content={
                "videos": videos
            },
            status_code=200
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取视频列表失败: {str(e)}"
        )
