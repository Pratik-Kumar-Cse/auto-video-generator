from enum import Enum


class ModelProvider(Enum):
    OPENAI = "openai"
    REQUESTY = "requesty"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
