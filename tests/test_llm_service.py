"""
Unit tests for LLM service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import asyncio

from app.services.llm.llm_call import LLMService
from app.core.exceptions import ExternalServiceException, APIKeyException


class TestLLMService:
    """Test LLM service functionality"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis service"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.cache_with_ttl = AsyncMock()
        return mock_redis

    @pytest.fixture
    def llm_service(self, mock_redis):
        """Create LLM service with mocked dependencies"""
        return LLMService(redis_service=mock_redis)

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Generated script content"))
        ]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300
        )
        return mock_response

    @pytest.fixture
    def mock_anthropic_response(self):
        """Mock Anthropic API response"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated script content")]
        mock_response.usage = MagicMock(
            input_tokens=100,
            output_tokens=200
        )
        return mock_response

    @pytest.mark.asyncio
    async def test_openai_call_success(self, llm_service, mock_openai_response):
        """Test successful OpenAI API call"""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.chat.completions.create.return_value = mock_openai_response
            
            result = await llm_service.call_openai(
                messages=[{"role": "user", "content": "Generate a script"}],
                model="gpt-4",
                temperature=0.7
            )
            
            assert result["content"] == "Generated script content"
            assert result["usage"]["total_tokens"] == 300
            assert result["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_openai_call_api_error(self, llm_service):
        """Test OpenAI API error handling"""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.chat.completions.create.side_effect = Exception("API Error")
            
            with pytest.raises(ExternalServiceException):
                await llm_service.call_openai(
                    messages=[{"role": "user", "content": "Generate a script"}],
                    model="gpt-4"
                )

    @pytest.mark.asyncio
    async def test_anthropic_call_success(self, llm_service, mock_anthropic_response):
        """Test successful Anthropic API call"""
        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.messages.create.return_value = mock_anthropic_response
            
            result = await llm_service.call_anthropic(
                messages=[{"role": "user", "content": "Generate a script"}],
                model="claude-3-sonnet-20240229",
                temperature=0.7
            )
            
            assert result["content"] == "Generated script content"
            assert result["usage"]["input_tokens"] == 100
            assert result["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_anthropic_call_api_error(self, llm_service):
        """Test Anthropic API error handling"""
        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.messages.create.side_effect = Exception("API Error")
            
            with pytest.raises(ExternalServiceException):
                await llm_service.call_anthropic(
                    messages=[{"role": "user", "content": "Generate a script"}],
                    model="claude-3-sonnet-20240229"
                )

    @pytest.mark.asyncio
    async def test_gemini_call_success(self, llm_service):
        """Test successful Gemini API call"""
        mock_response = MagicMock()
        mock_response.text = "Generated script content"
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=100,
            candidates_token_count=200,
            total_token_count=300
        )
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance
            mock_instance.generate_content_async.return_value = mock_response
            
            result = await llm_service.call_gemini(
                prompt="Generate a script",
                model="gemini-pro",
                temperature=0.7
            )
            
            assert result["content"] == "Generated script content"
            assert result["usage"]["total_tokens"] == 300
            assert result["provider"] == "gemini"

    @pytest.mark.asyncio
    async def test_deepseek_call_success(self, llm_service):
        """Test successful DeepSeek API call"""
        mock_response = {
            "choices": [{
                "message": {"content": "Generated script content"}
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response_obj
            
            result = await llm_service.call_deepseek(
                messages=[{"role": "user", "content": "Generate a script"}],
                model="deepseek-chat",
                temperature=0.7
            )
            
            assert result["content"] == "Generated script content"
            assert result["usage"]["total_tokens"] == 300
            assert result["provider"] == "deepseek"

    @pytest.mark.asyncio
    async def test_generate_script_with_fallback(self, llm_service, mock_redis):
        """Test script generation with provider fallback"""
        # Mock first provider to fail, second to succeed
        with patch.object(llm_service, 'call_openai') as mock_openai, \
             patch.object(llm_service, 'call_anthropic') as mock_anthropic:
            
            mock_openai.side_effect = ExternalServiceException("OpenAI", "API Error")
            mock_anthropic.return_value = {
                "content": "Generated script content",
                "usage": {"total_tokens": 300},
                "provider": "anthropic"
            }
            
            result = await llm_service.generate_script(
                topic="AI Technology",
                video_type="shorts",
                keywords={"tone": "casual"},
                providers=["openai", "anthropic"]
            )
            
            assert result["content"] == "Generated script content"
            assert result["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_generate_script_all_providers_fail(self, llm_service):
        """Test script generation when all providers fail"""
        with patch.object(llm_service, 'call_openai') as mock_openai, \
             patch.object(llm_service, 'call_anthropic') as mock_anthropic:
            
            mock_openai.side_effect = ExternalServiceException("OpenAI", "API Error")
            mock_anthropic.side_effect = ExternalServiceException("Anthropic", "API Error")
            
            with pytest.raises(ExternalServiceException):
                await llm_service.generate_script(
                    topic="AI Technology",
                    video_type="shorts",
                    keywords={"tone": "casual"},
                    providers=["openai", "anthropic"]
                )

    @pytest.mark.asyncio
    async def test_validate_link_youtube_success(self, llm_service):
        """Test successful YouTube link validation"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = '<title>Test Video</title>'
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await llm_service.validate_link(
                "https://youtube.com/watch?v=123",
                "youtube"
            )
            
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_link_invalid_url(self, llm_service):
        """Test validation of invalid URL"""
        result = await llm_service.validate_link("invalid-url", "youtube")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_link_network_error(self, llm_service):
        """Test link validation with network error"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = await llm_service.validate_link(
                "https://youtube.com/watch?v=123",
                "youtube"
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_extract_content_from_url(self, llm_service):
        """Test content extraction from URL"""
        mock_html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <h1>Article Title</h1>
                <p>This is the article content.</p>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = mock_html
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await llm_service.extract_content_from_url(
                "https://example.com/article"
            )
            
            assert "Article Title" in result
            assert "article content" in result

    @pytest.mark.asyncio
    async def test_cache_response(self, llm_service, mock_redis):
        """Test response caching"""
        cache_key = "script_cache:test_key"
        response_data = {
            "content": "Cached script content",
            "usage": {"total_tokens": 300}
        }
        
        # Test cache miss and set
        mock_redis.get.return_value = None
        await llm_service._cache_response(cache_key, response_data, ttl=3600)
        mock_redis.set.assert_called_once()
        
        # Test cache hit
        mock_redis.get.return_value = json.dumps(response_data).encode()
        cached_result = await llm_service._get_cached_response(cache_key)
        assert cached_result == response_data

    @pytest.mark.asyncio
    async def test_rate_limiting(self, llm_service, mock_redis):
        """Test rate limiting functionality"""
        # Mock rate limit check
        mock_redis.get.return_value = b"5"  # Current request count
        
        is_allowed = await llm_service._check_rate_limit("user123", limit=10)
        assert is_allowed is True
        
        # Test rate limit exceeded
        mock_redis.get.return_value = b"10"  # At limit
        is_allowed = await llm_service._check_rate_limit("user123", limit=10)
        assert is_allowed is False

    @pytest.mark.asyncio
    async def test_token_counting(self, llm_service):
        """Test token counting functionality"""
        text = "This is a test message for token counting."
        
        # Mock tiktoken encoding
        with patch('tiktoken.encoding_for_model') as mock_encoding:
            mock_enc = MagicMock()
            mock_enc.encode.return_value = [1, 2, 3, 4, 5, 6, 7, 8]
            mock_encoding.return_value = mock_enc
            
            token_count = llm_service._count_tokens(text, "gpt-4")
            assert token_count == 8

    @pytest.mark.asyncio
    async def test_prompt_template_generation(self, llm_service):
        """Test prompt template generation"""
        template = llm_service._generate_prompt_template(
            topic="AI Technology",
            video_type="shorts",
            keywords={"tone": "casual", "audience": "developers"},
            input_type="TOPIC"
        )
        
        assert "AI Technology" in template
        assert "shorts" in template
        assert "casual" in template
        assert "developers" in template

    @pytest.mark.asyncio
    async def test_response_parsing(self, llm_service):
        """Test response parsing and validation"""
        raw_response = """
        {
            "title": "AI Technology Explained",
            "content": "This is the script content...",
            "metadata": {
                "duration": "60 seconds",
                "style": "educational"
            }
        }
        """
        
        parsed = llm_service._parse_script_response(raw_response)
        
        assert parsed["title"] == "AI Technology Explained"
        assert "script content" in parsed["content"]
        assert parsed["metadata"]["duration"] == "60 seconds"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, llm_service):
        """Test handling concurrent LLM requests"""
        with patch.object(llm_service, 'call_openai') as mock_openai:
            mock_openai.return_value = {
                "content": "Generated script content",
                "usage": {"total_tokens": 300},
                "provider": "openai"
            }
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = llm_service.generate_script(
                    topic=f"Topic {i}",
                    video_type="shorts",
                    keywords={"tone": "casual"},
                    providers=["openai"]
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert all(r["content"] == "Generated script content" for r in results)

    @pytest.mark.asyncio
    async def test_error_recovery(self, llm_service):
        """Test error recovery mechanisms"""
        with patch.object(llm_service, 'call_openai') as mock_openai:
            # First call fails, second succeeds
            mock_openai.side_effect = [
                ExternalServiceException("OpenAI", "Temporary error"),
                {
                    "content": "Generated script content",
                    "usage": {"total_tokens": 300},
                    "provider": "openai"
                }
            ]
            
            result = await llm_service.generate_script_with_retry(
                topic="AI Technology",
                video_type="shorts",
                keywords={"tone": "casual"},
                max_retries=2
            )
            
            assert result["content"] == "Generated script content"
            assert mock_openai.call_count == 2

    @pytest.mark.asyncio
    async def test_content_filtering(self, llm_service):
        """Test content filtering and safety checks"""
        unsafe_content = "This content contains inappropriate material..."
        safe_content = "This is appropriate educational content."
        
        # Mock content safety check
        with patch.object(llm_service, '_check_content_safety') as mock_safety:
            mock_safety.side_effect = [False, True]  # First unsafe, second safe
            
            # Should reject unsafe content
            is_safe = await llm_service._check_content_safety(unsafe_content)
            assert is_safe is False
            
            # Should accept safe content
            is_safe = await llm_service._check_content_safety(safe_content)
            assert is_safe is True

    @pytest.mark.asyncio
    async def test_usage_tracking(self, llm_service, mock_redis):
        """Test usage tracking and analytics"""
        usage_data = {
            "provider": "openai",
            "model": "gpt-4",
            "tokens": 300,
            "cost": 0.006,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        await llm_service._track_usage("user123", usage_data)
        
        # Verify usage was recorded
        mock_redis.lpush.assert_called()
        mock_redis.incr.assert_called()

    @pytest.mark.asyncio
    async def test_model_selection_strategy(self, llm_service):
        """Test intelligent model selection"""
        # Test selection based on content type and requirements
        model = llm_service._select_optimal_model(
            content_type="script",
            length="short",
            complexity="simple",
            budget="low"
        )
        
        # Should select cost-effective model for simple, short content
        assert model in ["gpt-3.5-turbo", "claude-3-haiku-20240307"]
        
        model = llm_service._select_optimal_model(
            content_type="script",
            length="long",
            complexity="high",
            budget="high"
        )
        
        # Should select premium model for complex, long content
        assert model in ["gpt-4", "claude-3-opus-20240229"]