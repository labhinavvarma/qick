#!/bin/bash
# Quick Installation Commands for Healthcare API
# Copy and paste these commands one by one

# ==========================================
# STEP 1: Install Dependencies
# ==========================================
echo "📦 Installing dependencies..."

# Install websockets (fixes MCP module error)
python3.12 -m pip install websockets

# Install MCP packages
python3.12 -m pip install mcp fastmcp

# Install/upgrade scikit-learn (fixes version warning)
python3.12 -m pip install --upgrade scikit-learn==1.7.0

# Install FastAPI and related packages
python3.12 -m pip install fastapi uvicorn[standard] httpx requests

# Install Pydantic
python3.12 -m pip install pydantic pydantic-settings

# Or install everything at once from requirements.txt
python3.12 -m pip install -r requirements.txt

# ==========================================
# STEP 2: Verify Installation
# ==========================================
echo "✅ Verifying installations..."

python3.12 -m pip list | grep -E 'websockets|mcp|fastapi|scikit-learn|pydantic'

# ==========================================
# STEP 3: Run the Application
# ==========================================
echo "🚀 Starting the application..."

# Option 1: Direct run
python3.12 app.py

# Option 2: Using uvicorn with auto-reload (for development)
# uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# ==========================================
# TESTING COMMANDS
# ==========================================

# Test health endpoint
# curl http://localhost:8000/health

# Test simple prediction
# curl -X POST http://localhost:8000/predict-simple \
#   -H "Content-Type: application/json" \
#   -d '{"age":50,"sex":"male","chest_pain":"asymptomatic","resting_bp":120,"cholesterol":200,"max_heart_rate":150}'

# View API docs in browser
# Open: http://localhost:8000/docs

# ==========================================
# EXPECTED OUTPUT (After fixes)
# ==========================================
# ✅ Heart disease model loaded successfully
# ✅ MCP modules loaded successfully
# ✅ Healthcare endpoints: MCP mode
# INFO:     Uvicorn running on http://0.0.0.0:8000
