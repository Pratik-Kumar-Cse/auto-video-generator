#!/bin/bash

# FastAPI Video Generator - Local Development Server
# This script sets up and runs the FastAPI video generator server locally using Poetry

set -e  # Exit on any error

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check if Python is installed
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_error "Python 3.8+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Check if Poetry is installed
if ! command_exists poetry; then
    print_error "Poetry is not installed. Please install Poetry first."
    print_status "Install Poetry with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if MongoDB is installed and running (optional - can use cloud MongoDB)
MONGODB_REQUIRED=false
if [ "$MONGODB_REQUIRED" = true ]; then
    if ! command_exists mongod; then
        print_warning "MongoDB is not installed locally. Make sure MONGODB_URL in .env points to a valid MongoDB instance."
    fi
fi

# Check if Redis is installed and running (optional - can use cloud Redis)
REDIS_REQUIRED=false
if [ "$REDIS_REQUIRED" = true ]; then
    if ! command_exists redis-server; then
        print_warning "Redis is not installed locally. Make sure REDIS_URL in .env points to a valid Redis instance."
    fi
fi

print_success "All prerequisites are available"

# Set default values
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"
DEFAULT_ENV="development"

# Parse command line arguments
HOST=${1:-$DEFAULT_HOST}
PORT=${2:-$DEFAULT_PORT}
ENV=${3:-$DEFAULT_ENV}

print_status "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Environment: $ENV"

# Check if port is available
if ! check_port $PORT; then
    print_error "Port $PORT is already in use. Please choose a different port."
    print_status "Usage: $0 [host] [port] [environment]"
    print_status "Example: $0 0.0.0.0 8001 development"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success ".env file created"
    else
        print_warning ".env.example not found, creating basic .env file..."
        cat > .env << EOF
# Environment
ENVIRONMENT=development
DEBUG=true

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=video_generator

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs (add your keys)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=100MB

# Logging
LOG_LEVEL=INFO
EOF
        print_success "Basic .env file created"
    fi
fi

# Check if pyproject.toml exists
if [ ! -f pyproject.toml ]; then
    print_error "pyproject.toml not found. This project requires Poetry for dependency management."
    exit 1
fi

# Install dependencies with Poetry
print_status "Installing dependencies with Poetry..."
poetry install
print_success "Dependencies installed"

# Activate Poetry shell
print_status "Using Poetry virtual environment..."
print_success "Poetry environment ready"

# Check if external services are accessible
print_status "Checking external services..."

# Extract MongoDB URL from .env
if [ -f .env ]; then
    MONGODB_URL=$(grep "^MONGODB_URL=" .env | cut -d '=' -f2- | tr -d '"')
    REDIS_URL=$(grep "^REDIS_URL=" .env | cut -d '=' -f2- | tr -d '"')
    
    # Test MongoDB connection (optional)
    if [ ! -z "$MONGODB_URL" ]; then
        print_status "MongoDB URL configured: $MONGODB_URL"
    fi
    
    # Test Redis connection (optional)
    if [ ! -z "$REDIS_URL" ]; then
        print_status "Redis URL configured: $REDIS_URL"
    fi
fi

print_success "External services configuration checked"

# Start Celery worker in background (if Redis is available)
if [ ! -z "$REDIS_URL" ]; then
    print_status "Starting Celery worker..."
    poetry run celery -A app.tasks.celery_app worker --loglevel=info --detach &
    CELERY_WORKER_PID=$!
    print_success "Celery worker started (PID: $CELERY_WORKER_PID)"

    # Start Celery beat scheduler in background (for periodic tasks)
    print_status "Starting Celery beat scheduler..."
    poetry run celery -A app.tasks.celery_app beat --loglevel=info --detach &
    CELERY_BEAT_PID=$!
    print_success "Celery beat scheduler started (PID: $CELERY_BEAT_PID)"
else
    print_warning "Redis URL not configured. Celery workers will not start."
fi

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down services..."
    
    # Stop Celery processes
    if [ ! -z "$CELERY_WORKER_PID" ]; then
        kill $CELERY_WORKER_PID 2>/dev/null || true
    fi
    if [ ! -z "$CELERY_BEAT_PID" ]; then
        kill $CELERY_BEAT_PID 2>/dev/null || true
    fi
    
    # Kill any remaining celery processes
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "celery.*beat" 2>/dev/null || true
    
    # Poetry manages virtual environment automatically
    
    print_success "Cleanup completed"
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Start the FastAPI server
print_status "Starting FastAPI server..."
print_status "Server will be available at: http://$HOST:$PORT"
print_status "API documentation will be available at: http://$HOST:$PORT/docs"
print_status "Alternative docs at: http://$HOST:$PORT/redoc"
print_status ""
print_status "Press Ctrl+C to stop the server"
print_status ""

# Start the server with Poetry
poetry run uvicorn main:app \
    --host $HOST \
    --port $PORT \
    --reload \
    --log-level info \
    --access-log \
    --use-colors

# Note: The cleanup function will be called automatically when the script exits