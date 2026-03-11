#!/bin/bash

echo "========================================"
echo "SolarSnap Backend - Quick Start"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Check if requirements are installed
if [ ! -d "venv/lib/python*/site-packages/flask" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Check if database exists
if [ ! -f "solarsnap.db" ]; then
    echo "Initializing database..."
    python init_db.py
    echo ""
fi

# Start server
echo "Starting server..."
echo "Server will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""
python run.py
