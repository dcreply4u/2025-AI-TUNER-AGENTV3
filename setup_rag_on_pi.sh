#!/bin/bash
# Setup script for RAG AI Advisor on Raspberry Pi
# Run this on the Pi: bash setup_rag_on_pi.sh

echo "Setting up RAG AI Advisor dependencies..."
echo ""

# Install Python dependencies
echo "Installing chromadb..."
pip3 install --user chromadb 2>&1 | tail -10

echo ""
echo "Installing sentence-transformers..."
pip3 install --user sentence-transformers 2>&1 | tail -10

echo ""
echo "Installing ollama Python client..."
pip3 install --user ollama 2>&1 | tail -10

echo ""
echo "Checking if Ollama is installed..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
    echo "Checking for llama3.2:3b model..."
    if ollama list | grep -q "llama3.2:3b"; then
        echo "✅ Model llama3.2:3b is available"
    else
        echo "⚠️  Model not found. Installing..."
        ollama pull llama3.2:3b
    fi
else
    echo "⚠️  Ollama not installed. Install from https://ollama.ai"
    echo "   Or run: curl -fsSL https://ollama.ai/install.sh | sh"
fi

echo ""
echo "Running quick test..."
cd /home/aituner/AITUNER/2025-AI-TUNER-AGENTV3
python3 test_rag_quick.py

echo ""
echo "Setup complete!"


