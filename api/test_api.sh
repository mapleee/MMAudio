curl -X POST "http://localhost:8000/api/v1/generate-video" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "A tiger walking in snow", "aspect_ratio": "16:9", "loop": true}'