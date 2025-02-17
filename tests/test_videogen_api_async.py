import pytest
from fastapi.testclient import TestClient
import asyncio
from api.videogen_api_async import app
import aiohttp
from unittest.mock import patch, AsyncMock
import json

# 创建测试客户端
client = TestClient(app)

# 模拟API响应数据
MOCK_GENERATION_RESPONSE = {
    "id": "test_generation_id_123",
    "state": "pending"
}

MOCK_STATUS_RESPONSE_PENDING = {
    "id": "test_generation_id_123",
    "state": "pending"
}

MOCK_STATUS_RESPONSE_COMPLETED = {
    "id": "test_generation_id_123",
    "state": "completed",
    "video": {
        "url": "https://example.com/video.mp4"
    }
}

@pytest.fixture
def mock_aiohttp_session():
    """创建模拟的aiohttp会话"""
    async def mock_post(*args, **kwargs):
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value=MOCK_GENERATION_RESPONSE)
        return mock_response

    async def mock_get(*args, **kwargs):
        mock_response = AsyncMock()
        mock_response.status = 200
        # 第一次调用返回pending状态，第二次调用返回completed状态
        if not hasattr(mock_get, 'called'):
            mock_get.called = True
            mock_response.json = AsyncMock(return_value=MOCK_STATUS_RESPONSE_PENDING)
        else:
            mock_response.json = AsyncMock(return_value=MOCK_STATUS_RESPONSE_COMPLETED)
        return mock_response

    mock_session = AsyncMock()
    mock_session.post = mock_post
    mock_session.get = mock_get
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        yield mock_session

def test_create_video_generation():
    """测试创建视频生成任务"""
    response = client.post("/generate-video/", params={"prompt": "test prompt"})
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "queued"

def test_get_nonexistent_task_status():
    """测试获取不存在的任务状态"""
    response = client.get("/task-status/nonexistent_task")
    assert response.status_code == 404
    assert response.json()["detail"] == "任务不存在"

@pytest.mark.asyncio
async def test_full_video_generation_flow(mock_aiohttp_session):
    """测试完整的视频生成流程"""
    # 创建任务
    response = client.post("/generate-video/", params={"prompt": "test prompt"})
    assert response.status_code == 200
    task_data = response.json()
    task_id = task_data["task_id"]

    # 等待一小段时间让任务开始处理
    await asyncio.sleep(1)

    # 检查任务状态
    response = client.get(f"/task-status/{task_id}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["status"] in ["queued", "processing"]

    # 等待任务处理完成
    max_retries = 3
    for _ in range(max_retries):
        await asyncio.sleep(1)
        response = client.get(f"/task-status/{task_id}")
        status_data = response.json()
        if status_data["status"] == "completed":
            break

    # 验证最终状态
    assert status_data["status"] == "completed"
    assert "video_url" in status_data
    assert status_data["video_url"] == "https://example.com/video.mp4"

@pytest.mark.asyncio
async def test_concurrent_requests():
    """测试并发请求处理"""
    # 创建多个并发请求
    concurrent_requests = 7  # 超过最大并发数5
    responses = []
    
    for i in range(concurrent_requests):
        response = client.post("/generate-video/", params={"prompt": f"test prompt {i}"})
        responses.append(response)

    # 验证所有请求都被接受
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"

    # 验证任务队列中的任务数量
    await asyncio.sleep(1)
    tasks_in_process = sum(1 for task in responses if 
                          client.get(f"/task-status/{task.json()['task_id']}").json()["status"] == "processing")
    assert tasks_in_process <= 5  # 确保同时处理的任务不超过限制

if __name__ == "__main__":
    pytest.main(["-v"]) 