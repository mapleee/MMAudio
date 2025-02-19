from gradio_client import Client

def video2audio(video_path, user_id, task_id, prompt, negative_prompt):
	client = Client("http://0.0.0.0:7860/")
	print(f"生成有声视频: {video_path}")
	result = client.predict(
			video=video_path,
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
	print(f"生成有声视频完成: {result}")
	return result