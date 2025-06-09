#!/bin/bash

echo "🚀 Starting Noah HR Management API..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗄️ Initializing database..."
python3 init_db.py

echo "🌟 Starting API server..."
echo "📖 Swagger documentation will be available at: http://localhost:8181/docs"
echo "📚 ReDoc documentation will be available at: http://localhost:8181/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8181 