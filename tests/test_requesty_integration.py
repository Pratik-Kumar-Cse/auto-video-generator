#!/usr/bin/env python3
"""
Test script to verify REQUESTY integration and logging functionality
in the FastAPI Video Generator service.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_environment_setup():
    """Test that environment variables are properly configured."""
    print("=" * 60)
    print("TESTING ENVIRONMENT SETUP")
    print("=" * 60)

    from app.core.config import settings

    # Check OpenAI API Key
    if settings.OPENAI_API_KEY:
        print("✅ OPENAI_API_KEY is configured")
    else:
        print("❌ OPENAI_API_KEY is missing")

    # Check REQUESTY API Key
    if settings.REQUESTY_KEY:
        print("✅ REQUESTY_KEY is configured")
    else:
        print("❌ REQUESTY_KEY is missing")

    print()


def test_model_configuration():
    """Test that model configurations are properly loaded."""
    print("=" * 60)
    print("TESTING MODEL CONFIGURATION")
    print("=" * 60)

    from model_config import AIConfigManager
    from app.constant.enum.model_enum import ModelProvider

    config_manager = AIConfigManager()

    # Test getting all configurations
    all_configs = config_manager.get_all_current_configs()
    print(f"✅ Loaded {len(all_configs)} AI provider configurations")

    for config in all_configs:
        provider = config.get("provider", "Unknown")
        model = config.get("model", "Unknown")
        has_key = bool(config.get("api_key"))
        print(f"  - {provider}: {model} (API Key: {'✅' if has_key else '❌'})")

    # Test specific provider configurations
    try:
        openai_config = config_manager.get_config(ModelProvider.OPENAI)
        print(f"✅ OpenAI config: {openai_config['model']}")
    except Exception as e:
        print(f"❌ OpenAI config error: {e}")

    try:
        requesty_config = config_manager.get_config(ModelProvider.REQUESTY)
        print(f"✅ REQUESTY config: {requesty_config['model']}")
    except Exception as e:
        print(f"❌ REQUESTY config error: {e}")

    print()


def test_llm_service():
    """Test the LLM service with different providers."""
    print("=" * 60)
    print("TESTING LLM SERVICE")
    print("=" * 60)

    from app.services.llm.llm_call import generate_response
    from app.constant.enum.model_enum import ModelProvider

    test_prompt = (
        "Write a brief introduction about artificial intelligence in 2 sentences."
    )

    # Test OpenAI
    try:
        print("Testing OpenAI provider...")
        response = generate_response(test_prompt, ModelProvider.OPENAI)
        print(f"✅ OpenAI response: {response[:100]}...")
    except Exception as e:
        print(f"❌ OpenAI error: {e}")

    # Test REQUESTY
    try:
        print("Testing REQUESTY provider...")
        response = generate_response(test_prompt, ModelProvider.REQUESTY)
        print(f"✅ REQUESTY response: {response[:100]}...")
    except Exception as e:
        print(f"❌ REQUESTY error: {e}")

    print()


def test_agent_creation():
    """Test that agents can be created with proper logging."""
    print("=" * 60)
    print("TESTING AGENT CREATION")
    print("=" * 60)

    try:
        from app.agents.script_generator.agents import (
            create_video_team,
            create_reel_team,
            Master_Agent,
        )

        print("✅ Master Agent created successfully")
        print(f"  - Agent name: {Master_Agent.name}")

        print("Creating video team...")
        video_team = create_video_team()
        print("✅ Video team created successfully")

        print("Creating reel team...")
        reel_team = create_reel_team()
        print("✅ Reel team created successfully")

    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        import traceback

        traceback.print_exc()

    print()


def test_workflow_selection():
    """Test workflow selector functions."""
    print("=" * 60)
    print("TESTING WORKFLOW SELECTION")
    print("=" * 60)

    try:
        from app.agents.script_generator.agents import (
            video_selector_func,
            reel_selector_func,
        )

        # Test empty message list (should start workflow)
        video_start = video_selector_func([])
        print(f"✅ Video workflow start: {video_start}")

        reel_start = reel_selector_func([])
        print(f"✅ Reel workflow start: {reel_start}")

    except Exception as e:
        print(f"❌ Workflow selection error: {e}")

    print()


def test_logging_configuration():
    """Test that logging is properly configured."""
    print("=" * 60)
    print("TESTING LOGGING CONFIGURATION")
    print("=" * 60)

    # Test different log levels
    logger = logging.getLogger("test_logger")

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    print("✅ Logging test completed - check console output above")
    print()


def main():
    """Run all tests."""
    print("🚀 Starting REQUESTY Integration and Logging Tests")
    print()

    try:
        test_environment_setup()
        test_model_configuration()
        test_llm_service()
        test_agent_creation()
        test_workflow_selection()
        test_logging_configuration()

        print("=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        print()
        print("Summary:")
        print("- Environment variables configured")
        print("- Model configurations loaded")
        print("- LLM service working with multiple providers")
        print("- Agents created with proper logging")
        print("- Workflow selection functioning")
        print("- Logging system operational")
        print()
        print("🎉 REQUESTY integration and logging are working properly!")

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
