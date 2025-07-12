import logging
import os
from typing import Any, Dict, Optional

from autogen_core.models import ModelFamily
# validate_model_info is not available in current version
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Optional import for Anthropic
try:
    from autogen_ext.models.anthropic import AnthropicChatCompletionClient
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AnthropicChatCompletionClient = None

from app.core.config import settings

logger = logging.getLogger(__name__)

# settings is imported from app.core.config


class ModelFactory:
    """Factory class to create model clients based on configuration."""

    @staticmethod
    def create_model_client(model_config: Dict[str, Any]) -> Optional[Any]:
        """
        Creates a model client based on the provided configuration.

        Args:
            model_config: Dictionary containing model configuration parameters
                - provider: The model provider (e.g., "OpenAIChatCompletionClient")
                - model: The model name (e.g., "gpt-4o")
                - api_key: API key (optional if set in environment)
                - temperature: Temperature setting (optional)
                - max_tokens: Maximum tokens (optional)
                - model_info: Model capabilities (optional)
                - base_url: Base URL for API (optional)

        Returns:
            A model client instance or None if creation fails
        """
        try:
            provider = model_config.get("provider", "OpenAIChatCompletionClient")
            llm_type = model_config.get("llm_type", "openai")
            model = model_config.get("model")
            api_key = model_config.get("api_key")
            base_url = model_config.get("base_url")

            # Validate required fields
            if not model:
                logger.error("Model name is required in model configuration")
                return None

            # Handle OpenAI models
            if provider == "OpenAIChatCompletionClient":
                # Use environment variable if api_key not provided
                if not api_key:
                    api_key: str = settings.REQUESTY_KEY or settings.OPENAI_API_KEY

                # Extract optional parameters
                temperature = model_config.get("temperature")
                max_tokens = model_config.get("max_tokens")

                # Create model info with proper configuration
                model_info_config = model_config.get("model_info", {})

                # Determine model family based on model name
                model_family = ModelFactory._determine_model_family(model, llm_type)

                # Create comprehensive model info
                model_info = {
                    "vision": model_info_config.get(
                        "vision", ModelFactory._supports_vision(model, llm_type)
                    ),
                    "function_calling": model_info_config.get("function_calling", True),
                    "json_output": model_info_config.get("json_output", True),
                    "family": model_info_config.get("family", model_family),
                    "structured_output": model_info_config.get(
                        "structured_output", True
                    ),
                    # Critical: Set multiple_system_messages based on model capabilities
                    "multiple_system_messages": model_info_config.get(
                        "multiple_system_messages",
                        ModelFactory._supports_multiple_system_messages(
                            model, llm_type
                        ),
                    ),
                }

                # Validate model info - temporarily disabled
                # try:
                #     validate_model_info(model_info)
                # except Exception as e:
                #     logger.warning(f"Model info validation failed: {e}")
                #     # Use safe defaults if validation fails
                #     model_info["multiple_system_messages"] = True

                return OpenAIChatCompletionClient(
                    model=f"{llm_type}/{model}",
                    api_key=api_key,
                    base_url=base_url,
                    model_info=model_info,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            # Handle Anthropic models
            elif provider == "AnthropicChatCompletionClient":
                if not ANTHROPIC_AVAILABLE:
                    logger.error("Anthropic client requested but anthropic package not installed")
                    return None
                
                # Use environment variable if api_key not provided
                if not api_key:
                    api_key = os.getenv("ANTHROPIC_API_KEY", "")

                # Extract optional parameters
                temperature = model_config.get("temperature")
                max_tokens = model_config.get("max_tokens")

                # Create model info with proper configuration
                model_info_config = model_config.get("model_info", {})

                # Determine model family based on model name
                model_family = ModelFactory._determine_model_family(model, "anthropic")

                # Create comprehensive model info for Anthropic
                model_info = {
                    "vision": model_info_config.get(
                        "vision", ModelFactory._supports_vision(model, "anthropic")
                    ),
                    "function_calling": model_info_config.get("function_calling", True),
                    "json_output": model_info_config.get("json_output", True),
                    "family": model_info_config.get("family", model_family),
                    "structured_output": model_info_config.get(
                        "structured_output", True
                    ),
                    # Anthropic models generally support multiple system messages
                    "multiple_system_messages": model_info_config.get(
                        "multiple_system_messages", True
                    ),
                }

                # Validate model info - temporarily disabled
                # try:
                #     validate_model_info(model_info)
                # except Exception as e:
                #     logger.warning(f"Anthropic model info validation failed: {e}")
                #     # Use safe defaults if validation fails
                #     model_info["multiple_system_messages"] = True

                return AnthropicChatCompletionClient(
                    model=model,
                    api_key=api_key,
                    model_info=model_info,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            else:
                logger.warning(f"Model provider '{provider}' not supported yet")
                return None

        except Exception as e:
            logger.error(f"Error creating model client: {str(e)}")
            return None

    @staticmethod
    def _determine_model_family(model: str, llm_type: str) -> str:
        """
        Determine the model family based on model name and type.

        Args:
            model: The model name
            llm_type: The LLM type (openai, anthropic, etc.)

        Returns:
            The model family string
        """
        model_lower = model.lower()

        # OpenAI models
        if llm_type == "openai" or "gpt" in model_lower:
            if "gpt-4o" in model_lower:
                return ModelFamily.GPT_4O
            elif "gpt-4" in model_lower:
                if "gpt-41" in model_lower:
                    return ModelFamily.GPT_41
                elif "gpt-45" in model_lower:
                    return ModelFamily.GPT_45
                else:
                    return ModelFamily.GPT_4
            elif "gpt-3.5" in model_lower or "gpt-35" in model_lower:
                return ModelFamily.GPT_35
            elif "o1" in model_lower:
                return ModelFamily.O1
            elif "o3" in model_lower:
                return ModelFamily.O3
            elif "o4" in model_lower:
                return ModelFamily.O4
            elif "r1" in model_lower:
                return ModelFamily.R1

        # Anthropic models
        elif llm_type == "anthropic" or "claude" in model_lower:
            if "claude-3-5-sonnet" in model_lower:
                return ModelFamily.CLAUDE_3_5_SONNET
            elif "claude-3-5-haiku" in model_lower:
                return ModelFamily.CLAUDE_3_5_HAIKU
            elif "claude-3-7-sonnet" in model_lower:
                return ModelFamily.CLAUDE_3_7_SONNET
            elif "claude-3-opus" in model_lower:
                return ModelFamily.CLAUDE_3_OPUS
            elif "claude-3-sonnet" in model_lower:
                return ModelFamily.CLAUDE_3_SONNET
            elif "claude-3-haiku" in model_lower:
                return ModelFamily.CLAUDE_3_HAIKU
            elif "claude-4-opus" in model_lower:
                return ModelFamily.CLAUDE_4_OPUS
            elif "claude-4-sonnet" in model_lower:
                return ModelFamily.CLAUDE_4_SONNET

        # Gemini models
        elif "gemini" in model_lower:
            if "gemini-1.5-flash" in model_lower:
                return ModelFamily.GEMINI_1_5_FLASH
            elif "gemini-1.5-pro" in model_lower:
                return ModelFamily.GEMINI_1_5_PRO
            elif "gemini-2.0-flash" in model_lower:
                return ModelFamily.GEMINI_2_0_FLASH
            elif "gemini-2.5-flash" in model_lower:
                return ModelFamily.GEMINI_2_5_FLASH
            elif "gemini-2.5-pro" in model_lower:
                return ModelFamily.GEMINI_2_5_PRO

        # Default to unknown
        return ModelFamily.UNKNOWN

    @staticmethod
    def _supports_multiple_system_messages(model: str, llm_type: str) -> bool:
        """
        Determine if a model supports multiple system messages.

        Args:
            model: The model name
            llm_type: The LLM type

        Returns:
            True if the model supports multiple system messages
        """
        model_lower = model.lower()

        # Most modern models support multiple system messages
        # Only some older or specialized models don't

        # OpenAI models generally support multiple system messages
        if llm_type == "openai" or "gpt" in model_lower:
            # O1 models have restrictions on system messages
            if "o1" in model_lower:
                return False
            # Most other OpenAI models support multiple system messages
            return True

        # Anthropic models generally support multiple system messages
        elif llm_type == "anthropic" or "claude" in model_lower:
            return True

        # Gemini models support multiple system messages
        elif "gemini" in model_lower:
            return True

        # Default to True for safety (allows multiple system messages)
        return True

    @staticmethod
    def _supports_vision(model: str, llm_type: str) -> bool:
        """
        Determine if a model supports vision capabilities.

        Args:
            model: The model name
            llm_type: The LLM type

        Returns:
            True if the model supports vision
        """
        model_lower = model.lower()

        # OpenAI vision models
        if llm_type == "openai" or "gpt" in model_lower:
            return (
                "gpt-4o" in model_lower
                or "gpt-4-vision" in model_lower
                or "gpt-4-turbo" in model_lower
            )

        # Anthropic vision models
        elif llm_type == "anthropic" or "claude" in model_lower:
            # Claude 3 and later models support vision
            return "claude-3" in model_lower or "claude-4" in model_lower

        # Gemini models support vision
        elif "gemini" in model_lower:
            return True

        # Default to False
        return False

    @staticmethod
    def get_supported_providers() -> list[str]:
        """
        Get list of supported model providers.

        Returns:
            List of supported provider names
        """
        return ["OpenAIChatCompletionClient", "AnthropicChatCompletionClient"]

    @staticmethod
    def create_default_model_info(
        provider: str, model: str, llm_type: str = "openai"
    ) -> dict[str, Any]:
        """
        Create default model info for a given provider and model.

        Args:
            provider: The model provider
            model: The model name
            llm_type: The LLM type

        Returns:
            Default model info dictionary
        """
        model_family = ModelFactory._determine_model_family(model, llm_type)

        return {
            "vision": ModelFactory._supports_vision(model, llm_type),
            "function_calling": True,
            "json_output": True,
            "family": model_family,
            "structured_output": True,
            "multiple_system_messages": ModelFactory._supports_multiple_system_messages(
                model, llm_type
            ),
        }
