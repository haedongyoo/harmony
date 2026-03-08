#!/bin/sh
# Ollama 시작 후 모델 자동 pull

ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama to be ready..."
until ollama list > /dev/null 2>&1; do
  sleep 1
done

echo "Pulling llama3.2..."
ollama pull llama3.2

echo "Ollama ready."
wait $OLLAMA_PID
