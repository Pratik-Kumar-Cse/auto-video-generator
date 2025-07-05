# FastAPI Video Generator Service

A comprehensive FastAPI-based video generation service with script management, video processing, and advanced analytics capabilities.

## Features

- **Script Management**: AI-powered script generation with SSE streaming, regeneration, validation, and analytics
- **Video Processing**: Complete video generation workflow with community videos, upload integration, and metadata management
- **Authentication**: JWT-based authentication and user management
- **Subscription System**: Credit-based subscription management with usage tracking
- **Real-time Features**: Server-Sent Events for progress tracking
- **Multi-Provider Integration**: Support for multiple AI providers and upload services (YouTube, LinkedIn)
- **Advanced Analytics**: Comprehensive analytics and search functionality
- **Background Processing**: Celery-based task queue with Redis broker

## Technology Stack

- **Framework**: FastAPI with async/await support
- **Database**: MongoDB with Motor async driver
- **Cache/Queue**: Redis for caching and Celery task queues
- **Authentication**: JWT tokens with secure validation
- **Package Management**: Poetry for dependency management
- **Containerization**: Docker and Docker Compose
- **Background Tasks**: Celery with Redis broker
- **Real-time Communication**: Server-Sent Events (SSE)

## Prerequisites

- Python 3.9+
- Poetry (for dependency management)
- Docker and Docker Compose (for containerized deployment)
- MongoDB
- Redis

## Installation

### Using Poetry (Recommended)

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd fastapi-video-generator
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Install optional dependencies** (if needed):
   ```bash
   # For video processing
   poetry install --extras video
   
   # For cloud storage
   poetry install --extras cloud
   
   # For all optional features
   poetry install --extras all
   ```

5. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

### Using Docker Compose (Recommended for Development)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd fastapi-video-generator
   ```

2. **Start all services**:
   ```bash
   docker-compose up -d
   ```

This will start:
- FastAPI application (port 8000)
- MongoDB database (port 27017)
- Redis cache/broker (port 6379)
- Celery worker
- Celery beat scheduler
- Celery flower monitoring (port 5555)
- MongoDB Express (port 8081)
- Redis Commander (port 8082)

## Configuration

Create a `.env` file in the root directory:

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=video_generator

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Services
OPENAI_API_KEY=your-openai-key
CLAUDE_API_KEY=your-claude-key
GEMINI_API_KEY=your-gemini-key

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1

# Application
DEBUG=true
LOG_LEVEL=INFO
```

## Usage

### Development Server

Using Poetry:
```bash
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Server

```bash
poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Background Workers

Start Celery worker:
```bash
poetry run celery -A app.tasks.celery_app worker --loglevel=info
```

Start Celery beat scheduler:
```bash
poetry run celery -A app.tasks.celery_app beat --loglevel=info
```

Monitor with Celery Flower:
```bash
poetry run celery -A app.tasks.celery_app flower --port=5555
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### Scripts
- `POST /api/v1/scripts/generate` - Generate script with AI
- `GET /api/v1/scripts/stream/{script_id}` - SSE stream for script generation
- `GET /api/v1/scripts/` - List user scripts
- `GET /api/v1/scripts/{script_id}` - Get script details
- `PUT /api/v1/scripts/{script_id}` - Update script
- `DELETE /api/v1/scripts/{script_id}` - Delete script
- `POST /api/v1/scripts/{script_id}/regenerate` - Regenerate script
- `GET /api/v1/scripts/trending-topics` - Get trending topics
- `GET /api/v1/scripts/analytics` - Script analytics

### Videos
- `POST /api/v1/videos/generate` - Generate video
- `GET /api/v1/videos/` - List user videos
- `GET /api/v1/videos/{video_id}` - Get video details
- `PUT /api/v1/videos/{video_id}` - Update video
- `DELETE /api/v1/videos/{video_id}` - Delete video
- `GET /api/v1/videos/{video_id}/status` - Get generation status
- `POST /api/v1/videos/upload` - Upload video file
- `GET /api/v1/videos/community` - Get community videos
- `POST /api/v1/videos/{video_id}/like` - Like/unlike video
- `GET /api/v1/videos/analytics` - Video analytics

### Subscriptions
- `GET /api/v1/subscriptions/credits` - Get user credits
- `POST /api/v1/subscriptions/purchase` - Purchase credits
- `GET /api/v1/subscriptions/usage` - Get usage history

## Development

### Code Quality

Format code:
```bash
poetry run black .
```

Sort imports:
```bash
poetry run isort .
```

Lint code:
```bash
poetry run flake8 .
```

### Testing

Run tests:
```bash
poetry run pytest
```

Run tests with coverage:
```bash
poetry run pytest --cov=app
```

### Database Management

The service uses MongoDB with the following collections:
- `users` - User accounts and authentication
- `scripts` - Generated scripts and metadata
- `videos` - Video information and processing status
- `subscriptions` - User subscriptions and credits
- `memory_bank` - Knowledge base entries

## Monitoring

### Health Checks
- `GET /api/v1/health` - Application health status
- `GET /api/v1/health/db` - Database connectivity
- `GET /api/v1/health/redis` - Redis connectivity

### Monitoring Tools
- **Celery Flower**: http://localhost:5555 (task monitoring)
- **MongoDB Express**: http://localhost:8081 (database management)
- **Redis Commander**: http://localhost:8082 (Redis management)

## Architecture

The service follows a modular architecture:

```
app/
├── api/v1/endpoints/     # API route handlers
├── core/                 # Core configuration and utilities
├── models/              # Pydantic models and schemas
├── services/            # Business logic layer
├── tasks/               # Celery background tasks
├── db/                  # Database utilities and connections
└── main.py             # FastAPI application entry point
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License.