from gradio_client import Client

def video2audio(video_path, user_id, task_id):
	client = Client("http://0.0.0.0:7860/")
	result = client.predict(
			video=video_path,
			prompt="",
			negative_prompt="music",
			seed=-1,
			num_steps=25,
			cfg_strength=4.5,
			duration=80000000,
			user_id=user_id,
			task_id=task_id,
			api_name="/predict"
	)
	print(result)