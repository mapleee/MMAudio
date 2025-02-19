curl -X POST "http://0.0.0.0:7870/generate-soundful-video" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "A tiger walking in snow", "aspect_ratio": "1:1"}'

curl -X GET "http://0.0.0.0:7870/task/e4fbc69a-bdb7-4d7a-bab9-9c9f308db6cd"