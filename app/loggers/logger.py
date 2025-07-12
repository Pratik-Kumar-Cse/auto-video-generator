import logging
import os
import re
from typing import Any, Optional
from pathlib import Path


# Default log level if not specified or invalid
DEFAULT_LOG_LEVEL = logging.INFO

# Map log level names to their corresponding logging constants
LOG_LEVEL_MAPPING = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Fields to be masked in logs
SENSITIVE_FIELDS = ["api_key", "password", "token", "secret", "key"]

# Module-specific log levels from environment
MODULE_LOG_LEVELS = {
    "app.services": os.getenv("LOG_LEVEL_SERVICES", "INFO").upper(),
    "app.api": os.getenv("LOG_LEVEL_API", "INFO").upper(),
    "app.agents": os.getenv("LOG_LEVEL_AGENTS", "INFO").upper(),
    "app.tasks": os.getenv("LOG_LEVEL_TASKS", "INFO").upper(),
    "app.core": os.getenv("LOG_LEVEL_CORE", "INFO").upper(),
    "app.models": os.getenv("LOG_LEVEL_MODELS", "WARNING").upper(),
    "app.utils": os.getenv("LOG_LEVEL_UTILS", "WARNING").upper(),
    "app.middleware": os.getenv("LOG_LEVEL_MIDDLEWARE", "WARNING").upper(),
}

# External library log levels
EXTERNAL_LOG_LEVELS = {
    "pymongo": logging.ERROR,
    "pymongo.topology": logging.ERROR,
    "openai._base_client": logging.ERROR,
    "httpcore.http11": logging.ERROR,
    "httpcore.connection": logging.ERROR,
    "httpx": logging.ERROR,
    "uvicorn.access": logging.WARNING,
    "celery": logging.WARNING,
    "redis": logging.WARNING,
}


def get_log_level(module_name: Optional[str] = None) -> int:
    """Determine the log level based on environment variables and module."""
    # Check for module-specific log level first
    if module_name:
        for module_prefix, level_str in MODULE_LOG_LEVELS.items():
            if module_name.startswith(module_prefix):
                return LOG_LEVEL_MAPPING.get(level_str, DEFAULT_LOG_LEVEL)
    
    # Check global DEBUG flag
    if os.getenv("DEBUG", "false").lower() == "true":
        return logging.DEBUG
    
    # Check global LOG_LEVEL
    env_level = os.getenv("LOG_LEVEL", "INFO").upper()
    return LOG_LEVEL_MAPPING.get(env_level, DEFAULT_LOG_LEVEL)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for a specific module."""
    logger = logging.getLogger(name)
    
    # Set module-specific log level
    log_level = get_log_level(name)
    logger.setLevel(log_level)
    
    # Add context information
    if not logger.handlers:
        # If no handlers, it will inherit from root logger
        pass
    
    return logger


def setup_logger(log_file: str = "app.log") -> logging.Logger:
    """Set up and configure the root logger."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s "
        "[%(filename)s:%(lineno)s - %(funcName)s] - %(message)s"
    )
    console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create a log handler for file output
    file_handler = logging.FileHandler(
        filename=log_dir / log_file,
        mode="a",
        encoding="utf-8",
    )

    # Create a console handler for stdout output
    console_handler = logging.StreamHandler()

    # Apply the custom format to the handlers
    file_formatter = logging.Formatter(log_format)
    console_formatter = logging.Formatter(console_format)
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    file_handler.addFilter(filter_sensitive_fields)
    console_handler.addFilter(filter_sensitive_fields)

    # Create a logger and add the handlers
    root_logger = logging.getLogger()
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(get_log_level())

    # Configure external library loggers
    for logger_name, level in EXTERNAL_LOG_LEVELS.items():
        logging.getLogger(logger_name).setLevel(level)

    return root_logger


def setup_module_logger(
    module_name: str, log_file: Optional[str] = None
) -> logging.Logger:
    """Set up a module-specific logger with optional separate log file."""
    logger = logging.getLogger(module_name)
    logger.setLevel(get_log_level(module_name))
    
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create module-specific file handler
        file_handler = logging.FileHandler(
            filename=log_dir / log_file,
            mode="a",
            encoding="utf-8",
        )
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s "
            "[%(filename)s:%(lineno)s - %(funcName)s] - %(message)s"
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(filter_sensitive_fields)
        
        logger.addHandler(file_handler)
    
    return logger


def filter_sensitive_fields(record: logging.LogRecord) -> bool:
    """Filter sensitive fields from log records."""
    if isinstance(record.args, dict):
        record.args = {
            k: mask_sensitive_value(k, v) for k, v in record.args.items()
        }
    elif isinstance(record.args, tuple):
        record.args = tuple(
            mask_sensitive_value(str(arg), arg) for arg in record.args
        )

    if isinstance(record.msg, str):
        record.msg = remove_ansi_escape_sequences(record.msg)

    return True


def mask_sensitive_value(key: str, value: Any) -> Any:
    """Mask sensitive values."""
    return (
        "*****"
        if any(field in key.lower() for field in SENSITIVE_FIELDS)
        else value
    )


def remove_ansi_escape_sequences(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", text)
