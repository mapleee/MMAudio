from gradio_client import Client

client = Client("http://127.0.0.1:7860/")
result = client.predict(
		video="Hello!!",
		prompt="Hello!!",
		negative_prompt="music",
		seed=-1,
		num_steps=25,
		cfg_strength=4.5,
		duration=8,
		api_name="/predict"
)
print(result)