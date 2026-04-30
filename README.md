# RoboCop — Wearable Personal AI Companion

An always-on wearable AI system that sees, hears, and understands context to act as a personal mentor and companion throughout your day.

## Hardware Stack
- NVIDIA Jetson Orin Nano Super (67 TOPS)
- Luxonis OAK-D Lite (vision + depth)
- ReSpeaker XVF3800 USB (audio input)
- Shokz OpenRun Pro 2 (audio output)
- Polar H10 (biometrics)
- Waveshare 3.5" HDMI display

## Software Stack
- JetPack 6.2.1 / Ubuntu 22.04
- CUDA 12.6 / TensorRT 10.3
- Ollama (local LLM)
- DepthAI (OAK-D pipeline)
- OpenAI Whisper (speech to text)
- Piper TTS (text to speech)
- ChromaDB (memory/vector store)

## Architecture
perception → context engine → LLM reasoning → response → audio output

## Setup
See docs/setup.md for full setup instructions.

## Project Status
🔧 In active development
