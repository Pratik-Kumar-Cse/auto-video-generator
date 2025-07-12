# Server-Sent Events (SSE) Implementation

This document describes the Server-Sent Events (SSE) implementation for the FastAPI Video Generation Service, ported from the python-backend Flask implementation.

## Overview

The SSE implementation provides real-time communication between the server and clients, allowing the server to push updates to connected clients without requiring polling. This is particularly useful for:

- Script generation progress updates
- Video processing status updates
- Real-time notifications
- System messages and alerts

## Architecture

### Components

1. **SSE Manager** (`app/helper/sse_manager.py`)
   - Singleton class managing client connections
   - Thread-safe client queue management
   - Event broadcasting and targeted messaging

2. **SSE Service** (`app/services/sse_service.py`)
   - High-level service for sending different types of events
   - Integration with existing services
   - Predefined event types and data structures

3. **SSE Endpoints** (`app/api/v1/endpoints/sse.py`)
   - FastAPI endpoints for SSE connections
   - Authentication and client management
   - Event triggering and broadcasting

4. **SSE Models** (`app/models/sse.py`)
   - Pydantic models for request/response validation
   - Event data structures
   - Type definitions

5. **Auth Utils** (`app/utils/auth_utils.py`)
   - JWT token handling
   - User authentication and authorization
   - Token encryption/decryption

## API Endpoints

### Core SSE Endpoints

#### 1. Connect to SSE Stream
```
GET /api/v1/sse/events?token={auth_token}
```
- Establishes SSE connection for authenticated user
- Returns `text/event-stream` response
- Requires valid authentication token

#### 2. Trigger Event for Specific Client
```
POST /api/v1/sse/trigger/{client_id}
```
- Sends event to specific connected client
- Requires event type and data in request body

#### 3. Broadcast Event to All Clients
```
POST /api/v1/sse/broadcast
```
- Broadcasts event to all connected clients
- Useful for system-wide notifications

#### 4. Get SSE Status
```
GET /api/v1/sse/status
```
- Returns current SSE service status
- Shows connected clients count and IDs

#### 5. Send Notification
```
POST /api/v1/sse/send-notification/{client_id}
```
- Sends notification to specific client
- Supports different notification types (info, warning, error, success)

#### 6. Send Progress Update
```
POST /api/v1/sse/send-progress-update/{client_id}
```
- Sends progress update for ongoing tasks
- Includes progress percentage and current step

#### 7. Disconnect Client
```
DELETE /api/v1/sse/disconnect/{client_id}
```
- Forcefully disconnects a specific client

### Demo Endpoints

#### 1. Demo Script Generation
```
POST /api/v1/sse/demo/script-generation/{client_id}
```
- Simulates script generation with progress updates
- Useful for testing SSE functionality

#### 2. Demo Video Processing
```
POST /api/v1/sse/demo/video-processing/{client_id}
```
- Simulates video processing with status updates
- Shows different processing stages

#### 3. Demo Notifications
```
POST /api/v1/sse/demo/notifications/{client_id}
```
- Sends multiple demo notifications
- Tests different notification types

## Event Types

The implementation supports several predefined event types:

- `video_stream` - Video processing updates
- `script_generation` - Script generation progress
- `processing_update` - General processing updates
- `notification` - User notifications
- `system_message` - System-wide messages
- `keep-alive` - Connection keep-alive
- `error` - Error events
- `completed` - Task completion events
- `progress` - Progress updates

## Usage Examples

### Client-Side JavaScript

```javascript
// Connect to SSE stream
const eventSource = new EventSource('/api/v1/sse/events?token=YOUR_AUTH_TOKEN');

// Listen for script generation updates
eventSource.addEventListener('message', function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'script_generation') {
        console.log('Script generation progress:', data.data.progress);
        updateProgressBar(data.data.progress);
    }
});

// Handle connection errors
eventSource.onerror = function(event) {
    console.error('SSE connection error:', event);
};

// Close connection when done
eventSource.close();
```

### Server-Side Usage

```python
from app.services.sse_service import sse_service

# Send script generation update
sse_service.send_script_generation_update(
    client_id="user_123",
    task_id="script_456",
    status="processing",
    progress=75.0,
    message="Generating conclusion..."
)

# Send notification
sse_service.send_notification(
    client_id="user_123",
    title="Script Ready",
    message="Your script has been generated successfully!",
    notification_type="success"
)

# Broadcast system message
sse_service.send_system_message(
    message="System maintenance scheduled for tonight",
    level="warning"
)
```

## Authentication

The SSE implementation uses JWT tokens for authentication:

1. Client must provide valid authentication token as query parameter
2. Token is validated and user information is extracted
3. Client ID is derived from user ID for connection management
4. Invalid or expired tokens result in 401 Unauthorized response

## Error Handling

The implementation includes comprehensive error handling:

- Connection errors are logged and reported to clients
- Invalid tokens result in proper HTTP error responses
- Client disconnections are handled gracefully
- Queue overflow protection prevents memory issues

## Configuration

Key configuration settings in `app/core/config.py`:

- `TOKEN_EXPIRY_IN_HOUR` - JWT token expiration time
- `SECRET_KEY` - Secret key for token encryption
- `CORS_ORIGINS` - Allowed origins for CORS

## Testing

Use the demo endpoints to test SSE functionality:

1. Start the FastAPI server
2. Connect to SSE stream with valid token
3. Trigger demo events using the demo endpoints
4. Observe real-time updates in the client

## Integration with Existing Services

The SSE service integrates seamlessly with existing services:

- Script generation service can send progress updates
- Video processing service can send status updates
- Notification system can send real-time alerts
- System monitoring can broadcast maintenance messages

## Performance Considerations

- Uses thread-safe queue management for concurrent clients
- Implements keep-alive messages to maintain connections
- Includes queue size limits to prevent memory issues
- Graceful client cleanup on disconnection

## Security Features

- JWT token-based authentication
- Token encryption for enhanced security
- Client-specific event targeting
- CORS protection for cross-origin requests

## Monitoring and Logging

- Comprehensive logging for debugging and monitoring
- Client connection/disconnection tracking
- Event delivery status logging
- Error reporting and tracking

## Future Enhancements

Potential improvements for the SSE implementation:

1. **Redis Integration** - Store client connections in Redis for scalability
2. **Rate Limiting** - Implement rate limiting for event sending
3. **Message Persistence** - Store messages for offline clients
4. **Clustering Support** - Support for multiple server instances
5. **WebSocket Fallback** - Fallback to WebSockets for better browser support
6. **Message Acknowledgment** - Confirm message delivery
7. **Custom Event Filters** - Allow clients to subscribe to specific event types

## Troubleshooting

Common issues and solutions:

1. **Connection Drops**
   - Check network connectivity
   - Verify token validity
   - Monitor server logs for errors

2. **Missing Events**
   - Verify client is connected
   - Check event targeting (client_id)
   - Monitor queue status

3. **Authentication Errors**
   - Verify token format and validity
   - Check token expiration
   - Ensure proper secret key configuration

4. **Performance Issues**
   - Monitor connected clients count
   - Check queue sizes
   - Review server resource usage