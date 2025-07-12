from typing import Dict, List, Optional, Tuple, TypedDict

from app.core.config import settings
from app.constant.enum.model_enum import ModelProvider


class ModelConfigDict(TypedDict, total=False):
    model: str
    api_key: str
    base_url: Optional[str]
    api_type: Optional[str]
    tags: List[str]
    temperature: float
    top_p: Optional[float]
    max_tokens: Optional[int]


# Default models for each provider
default_openai_model = "gpt-4o"
default_requesty_model = "openai/gpt-4o"
default_gemini_model = "gemini-2.0-flash-exp"
default_claude_model = "claude-3-5-sonnet-20241022"
default_deepseek_model = "deepseek-chat"


default_gemini_models = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash-001",
    "gemini-1.5-pro-latest",
    "gemini-pro",
]


# Base configurations for each model
MODEL_CONFIGS: Dict[ModelProvider, Dict[str, dict]] = {
    ModelProvider.OPENAI: {
        # "o3-mini": {"tags": ["o3-mini", "openai"], "is_default": True},
        "gpt-4o": {"tags": ["gpt-4o", "openai"], "is_default": True},
        "gpt-4-turbo": {"tags": ["gpt4", "turbo"]},
        "gpt-3.5-turbo": {"tags": ["gpt3", "turbo"]},
        "gpt-4-vision-preview": {"tags": ["gpt4", "vision"]},
    },
    ModelProvider.REQUESTY: {
        "requesty-chat": {
            "base_url": "https://api.requesty.com/v1",
            "api_type": "requesty",
            "temperature": 0.7,
            "max_tokens": 4000,
            "tags": ["requesty", "chat"],
            "is_default": True,
        },
    },
    ModelProvider.GOOGLE: {
        "gemini-2.0-flash-exp": {"api_type": "google", "is_default": True},
        "gemini-pro": {"api_type": "google"},
        "gemini-pro-vision": {"api_type": "google"},
    },
    ModelProvider.ANTHROPIC: {
        "claude-3-haiku-20240307": {
            "base_url": "https://api.anthropic.com/v1/messages",
            "tags": ["claude", "haiku"],
        },
        "claude-3-opus-20240229": {
            "base_url": "https://api.anthropic.com/v1/messages",
            "tags": ["claude", "opus"],
            "is_default": True,
        },
    },
    ModelProvider.DEEPSEEK: {
        "deepseek-chat": {
            "base_url": "https://api.deepseek.com/v1",
            "api_type": "deepseek",
            "temperature": 0.5,
            "top_p": 0.2,
            "max_tokens": 10000,
            "tags": ["deepseek"],
            "is_default": True,
        },
    },
}


class AIConfigManager:
    def __init__(self):
        self.api_keys = {
            ModelProvider.OPENAI: settings.OPENAI_API_KEY,
            ModelProvider.REQUESTY: settings.REQUESTY_KEY,
            ModelProvider.ANTHROPIC: settings.CLAUDE_KEY,
            ModelProvider.GOOGLE: settings.GEMINI_API_KEY,
            ModelProvider.DEEPSEEK: settings.DEEPSEEK_API,
        }
        self.current_models = {
            provider: self._get_default_model(provider) for provider in ModelProvider
        }

    def _get_default_model(self, provider: ModelProvider) -> str:
        provider_configs = MODEL_CONFIGS[provider]
        return next(
            (
                model
                for model, config in provider_configs.items()
                if config.get("is_default")
            ),
            next(iter(provider_configs)),
        )

    def get_model_config(
        self, model_name: str
    ) -> Optional[Tuple[ModelProvider, ModelConfigDict]]:
        for provider, models in MODEL_CONFIGS.items():
            if model_name in models:
                config = models[model_name].copy()
                config.pop("is_default", None)
                return provider, {
                    "model": model_name,
                    "api_key": self.api_keys[provider],
                    **config,
                }
        return None

    def get_provider_configs(
        self, provider: ModelProvider = ModelProvider.OPENAI
    ) -> List[ModelConfigDict]:
        return [
            {
                "model": model_name,
                "api_key": self.api_keys[provider],
                **{k: v for k, v in config.items() if k != "is_default"},
            }
            for model_name, config in MODEL_CONFIGS[provider].items()
        ]

    def get_current_config(self, provider: ModelProvider) -> ModelConfigDict:
        model_name = self.current_models[provider]
        _, config = self.get_model_config(model_name)
        return config

    def select_model(
        self, provider: ModelProvider, model_name: str
    ) -> Optional[ModelConfigDict]:
        if model_name in MODEL_CONFIGS[provider]:
            self.current_models[provider] = model_name
            return self.get_current_config(provider)
        return None

    def get_available_models(self, provider: ModelProvider) -> List[str]:
        return list(MODEL_CONFIGS[provider].keys())

    def get_all_current_configs(self) -> List[ModelConfigDict]:
        return [self.get_current_config(provider) for provider in ModelProvider]
