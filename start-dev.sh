#!/bin/bash

# MedVaani Development Startup Script
# This script starts both the FastAPI backend and React frontend in development mode

set -e  # Exit on any error

echo "🩺 Starting MedVaani Development Environment"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi

print_status "Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python version: $PYTHON_VERSION"

print_status "Checking Node.js version..."
NODE_VERSION=$(node --version)
print_success "Node.js version: $NODE_VERSION"

# Install Python dependencies if needed
print_status "Checking Python dependencies..."
if [ ! -f "requirements-web.txt" ]; then
    print_error "requirements-web.txt not found. Please run this script from the project root."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements-web.txt
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
print_success "Python dependencies installed"

# Install Node.js dependencies
print_status "Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    print_status "Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
    print_success "Node.js dependencies installed"
else
    print_success "Node.js dependencies already installed"
fi

# Create environment file for frontend if it doesn't exist
if [ ! -f "frontend/.env.local" ]; then
    print_status "Creating frontend environment file..."
    cp frontend/.env.example frontend/.env.local
    print_success "Frontend environment file created"
fi

# Function to cleanup background processes
cleanup() {
    print_status "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    print_success "Services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_status "Starting services..."

# Start backend server
print_status "Starting FastAPI backend server..."
cd web
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..
print_success "Backend server started (PID: $BACKEND_PID)"

# Wait a moment for backend to start
sleep 2

# Start frontend development server
print_status "Starting React frontend development server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..
print_success "Frontend server started (PID: $FRONTEND_PID)"

print_success "🚀 MedVaani development environment is running!"
echo ""
echo "📍 Services:"
echo "   • Backend API: http://localhost:8000"
echo "   • Frontend App: http://localhost:3000"
echo "   • API Documentation: http://localhost:8000/docs"
echo ""
echo "🔧 Development URLs:"
echo "   • Health Check: http://localhost:8000/api/health-check"
echo "   • WebSocket Health: ws://localhost:8000/ws/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes to finish
wait $BACKEND_PID $FRONTEND_PID
