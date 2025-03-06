from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from google.cloud import storage
from typing import Optional
import os
import uuid
from pathlib import Path

# 在创建 storage_client 之前设置凭据
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/root/.config/gcloud/application_default_credentials.json"

router = APIRouter(
    prefix="/storage",
    tags=["storage"],
    responses={404: {"description": "Not found"}},
)

def generate_safe_filename(original_filename: str, user_id: str) -> str:
    """Generate a safe filename using UUID and original extension."""
    # 获取原始文件扩展名
    ext = Path(original_filename).suffix.lower()
    # 生成UUID
    unique_id = str(uuid.uuid4())
    # 构建新的文件名: user_id/uuid.ext
    return f"{user_id}/{unique_id}{ext}"

class BlobUploadRequest(BaseModel):
    bucket_name: str = Field("soundful", description="The ID of your GCS bucket")
    source_file_name: str = Field(..., description="The path to your file to upload")
    user_id: str = Field(..., description="User ID for organizing files")

class BlobDownloadRequest(BaseModel):
    bucket_name: str = Field("soundful", description="The ID of your GCS bucket")
    source_blob_name: str = Field(..., description="The ID of your GCS object")
    user_id: str = Field(..., description="User ID for organizing files")

class BlobResponse(BaseModel):
    status: str
    message: str
    file_url: Optional[str] = None

@router.post("/upload", response_model=BlobResponse)
async def upload_blob_endpoint(request: BlobUploadRequest):
    """Uploads a file to the bucket."""
    try:
        # 生成安全的文件名
        safe_filename = generate_safe_filename(
            request.source_file_name,
            request.user_id
        )
        
        # 构建完整的目标路径
        destination_blob_name = f"public/uploads/{safe_filename}"
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(request.bucket_name)
        blob = bucket.blob(destination_blob_name)

        generation_match_precondition = 0
        blob.upload_from_filename(
            request.source_file_name, 
            if_generation_match=generation_match_precondition
        )

        # 构建文件的公共URL
        file_url = f"https://storage.googleapis.com/{request.bucket_name}/{destination_blob_name}"

        return BlobResponse(
            status="success",
            message=f"File uploaded successfully",
            file_url=file_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download", response_model=BlobResponse)
async def download_blob_endpoint(request: BlobDownloadRequest):
    """Downloads a blob from the bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(request.bucket_name)
        blob = bucket.blob(request.source_blob_name)
        destination_file_name = f"/workspace/tmp/{request.user_id}/{os.path.basename(request.source_blob_name)}"
        blob.download_to_filename(destination_file_name)

        return BlobResponse(
            status="success",
            message=f"File downloaded successfully",
            file_url=destination_file_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 