import os
from gradio_client import Client
# from api.video_transport_router import download_blob_endpoint, BlobDownloadRequest, upload_blob_endpoint, BlobUploadRequest
from api.utils.url_utils import remove_storage_prefix, add_storage_prefix
from api.video_transport import download_blob, upload_blob

def video2audio(video_path, user_id, task_id, prompt="", negative_prompt="music"):
	client = Client("http://0.0.0.0:7860/")
	print(f"生成有声视频: {video_path}")

	if video_path.startswith("https://"):
		# 移除storage前缀
		source_blob_name = remove_storage_prefix(video_path)
		print(f"开始下载视频文件: {source_blob_name}")
		local_file_path = download_blob(
			bucket_name="soundful",
			source_blob_name=source_blob_name,
			destination_file_name=f"/workspace/tmp/{user_id}/{os.path.basename(source_blob_name)}"
		)
		print(f"下载视频文件完成: {local_file_path}")
	else:
		local_file_path = video_path

	result = client.predict(
			video=local_file_path,
			prompt=prompt if prompt else "",
			negative_prompt=negative_prompt if negative_prompt else "music",
			seed=-1,
			num_steps=25,
			cfg_strength=4.5,
			duration=80000000,
			user_id=user_id,
			task_id=task_id,
			api_name="/predict"
	)
	print(f"生成有声视频完成: {result}, user_id: {user_id}, task_id: {task_id}")

	# 上传视频文件到GCS
	upload_result = upload_blob(
		bucket_name="soundful",
		source_file_name=result,
		destination_blob_name=f"public/uploads/{user_id}/{os.path.basename(result)}"
	)

	final_url = add_storage_prefix(upload_result)
	print(f"上传有声视频文件到GCS完成: {final_url}")

	return final_url