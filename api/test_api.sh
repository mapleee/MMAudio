curl -X POST "http://0.0.0.0:7870/generate-soundful-video" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "A tiger walking in snow", "aspect_ratio": "1:1"}'

curl -X GET "http://0.0.0.0:7870/task/e4fbc69a-bdb7-4d7a-bab9-9c9f308db6cd"

curl -X POST "http://0.0.0.0:7880/video2audio" \
     -H "Content-Type: application/json" \
     -d '{"video_path": "/workspace/tmp/00000000000000000000000000000012/soundful_video_ff399c40-f9ee-46b6-8043-b51ddee54e73.mp4", "user_id": "00000000000000000000000000000012", "prompt": "A tiger walking in snow", "negative_prompt": "music"}'

curl -X GET "http://0.0.0.0:7880/task/d90bd0d7-6e67-493a-9cbe-146b59a2eaeb"