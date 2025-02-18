curl -X POST "http://0.0.0.0:7870/generate-soundful-video" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "A tiger walking in snow", "aspect_ratio": "1:1"}'