curl -X POST "http://0.0.0.0:7870/generate-soundful-video" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "A tiger walking in snow", "aspect_ratio": "1:1"}'

curl -X GET "http://0.0.0.0:7870/task/7a6e4b03-9a7c-42bd-a3bc-e08fc5e0c294"