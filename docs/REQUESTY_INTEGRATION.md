# REQUESTY Integration Guide

This document explains how to use the REQUESTY API provider in the FastAPI Video Generator service.

## Overview

REQUESTY has been added as an additional AI provider alongside OpenAI, Claude, Gemini, and DeepSeek. It provides an OpenAI-compatible API interface for generating video scripts, search terms, and other content.

## Configuration

### Environment Variables

Add the following environment variable to your `.env` file:

```bash
REQUESTY_KEY=your-requesty-api-key-here
```

### Model Configuration

The REQUESTY provider is configured with the following default settings:

- **Model**: `requesty-chat`
- **Base URL**: `https://api.requesty.com/v1`
- **Temperature**: `0.7`
- **Max Tokens**: `4000`
- **API Type**: `requesty`

## Usage

### Basic Usage

```python
from app.constant.enum.model_enum import ModelProvider
from app.services.llm.llm_call import generate_response

# Generate content using REQUESTY
response = generate_response(
    prompt="Create a video script about renewable energy",
    provider=ModelProvider.REQUESTY
)
```

### Available Providers

The system now supports the following providers:

- `ModelProvider.OPENAI` - OpenAI GPT models
- `ModelProvider.REQUESTY` - REQUESTY API (NEW)
- `ModelProvider.GOOGLE` - Google Gemini models
- `ModelProvider.ANTHROPIC` - Claude models
- `ModelProvider.DEEPSEEK` - DeepSeek models

### Example Script

Run the example script to test REQUESTY integration:

```bash
cd fastapi-video-generator
python examples/requesty_usage.py
```

## API Endpoints

All existing API endpoints that support AI model selection now include REQUESTY as an option:

### Script Generation

```bash
POST /api/v1/scripts/generate
{
    "topic": "Climate Change Solutions",
    "video_type": "educational",
    "provider": "requesty",
    "keywords": ["sustainability", "environment"]
}
```

### Video Generation

```bash
POST /api/v1/videos/generate
{
    "script_id": "script_id_here",
    "provider": "requesty",
    "quality": "1080p"
}
```

## Configuration Details

### Model Configuration

The REQUESTY provider is defined in `model_config.py`:

```python
ModelProvider.REQUESTY: {
    "requesty-chat": {
        "base_url": "https://api.requesty.com/v1",
        "api_type": "requesty",
        "temperature": 0.7,
        "max_tokens": 4000,
        "tags": ["requesty", "chat"],
        "is_default": True,
    },
}
```

### Settings Configuration

The API key is managed in `app/core/config.py`:

```python
REQUESTY_KEY: Optional[str] = Field(
    default=None, 
    description="Requesty API key"
)
```

## Error Handling

The REQUESTY provider includes the same error handling as other providers:

- **API Key Missing**: Configuration error if `REQUESTY_KEY` is not set
- **API Errors**: Wrapped in `ExternalServiceException`
- **Rate Limiting**: Handled according to REQUESTY API limits
- **Timeout**: Configurable timeout for requests

## Testing

### Unit Tests

The test suite includes REQUESTY provider tests:

```bash
# Run all tests
pytest tests/

# Run specific LLM tests
pytest tests/test_llm_service.py
```

### Integration Testing

Test the integration with:

```bash
# Test configuration
python -c "from app.core.config import settings; print(f'REQUESTY_KEY configured: {bool(settings.REQUESTY_KEY)}')"

# Test model configuration
python -c "from model_config import AIConfigManager; mgr = AIConfigManager(); print(mgr.api_keys)"
```

## Troubleshooting

### Common Issues

1. **Missing API Key**
   ```
   Error: REQUESTY_KEY is not configured
   Solution: Add REQUESTY_KEY to your .env file
   ```

2. **API Connection Error**
   ```
   Error: Connection to REQUESTY API failed
   Solution: Check your internet connection and API key validity
   ```

3. **Rate Limiting**
   ```
   Error: Rate limit exceeded
   Solution: Implement retry logic or reduce request frequency
   ```

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger("app.services.llm").setLevel(logging.DEBUG)
```

## Migration Guide

### From OpenAI Only

If you were previously using only OpenAI, you can now:

1. Add REQUESTY_KEY to your environment
2. Update your code to specify `provider=ModelProvider.REQUESTY`
3. Test the integration with the example script

### Fallback Strategy

Implement provider fallback:

```python
providers = [ModelProvider.REQUESTY, ModelProvider.OPENAI]
for provider in providers:
    try:
        response = generate_response(prompt, provider=provider)
        break
    except Exception as e:
        print(f"Provider {provider} failed: {e}")
        continue
```

## Performance Considerations

- **Token Usage**: REQUESTY tokens are tracked separately from OpenAI
- **Rate Limits**: Each provider has independent rate limits
- **Response Time**: May vary between providers
- **Cost**: Monitor usage across all providers

## Security

- **API Keys**: Store securely in environment variables
- **Logging**: API keys are masked in logs
- **Validation**: Input validation applies to all providers
- **Rate Limiting**: Implemented per provider

## Support

For issues related to:
- **REQUESTY API**: Contact REQUESTY support
- **Integration**: Check this documentation and example scripts
- **Configuration**: Review environment variables and model config

## Changelog

### v1.1.0
- Added REQUESTY provider support
- Updated model configuration system
- Added example scripts and documentation
- Enhanced error handling for multiple providers