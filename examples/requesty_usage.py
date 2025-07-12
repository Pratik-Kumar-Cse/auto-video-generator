#!/usr/bin/env python3
"""
Example script demonstrating how to use the REQUESTY provider
in the FastAPI Video Generator service.
"""

import asyncio
import os
import sys

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.constant.enum.model_enum import ModelProvider
from app.services.llm.llm_call import generate_response
from app.core.config import settings


async def main():
    """
    Example usage of the REQUESTY provider for generating content.
    """
    print("FastAPI Video Generator - REQUESTY Provider Example")
    print("=" * 50)

    # Check if REQUESTY_KEY is configured
    if not settings.REQUESTY_KEY:
        print("❌ REQUESTY_KEY is not configured in environment variables.")
        print("Please set REQUESTY_KEY in your .env file.")
        return

    print(f"✅ REQUESTY_KEY is configured: {settings.REQUESTY_KEY[:10]}...")

    # Example 1: Generate a simple script
    print("\n📝 Example 1: Generating a video script using REQUESTY")
    print("-" * 40)

    prompt = """
    Create a 30-second video script about the benefits of renewable energy.
    Make it engaging and informative for a general audience.
    """

    try:
        response = generate_response(prompt, provider=ModelProvider.REQUESTY)
        print("Generated Script:")
        print(response)
    except Exception as e:
        print(f"❌ Error generating script: {str(e)}")

    # Example 2: Generate search terms
    print("\n🔍 Example 2: Generating search terms using REQUESTY")
    print("-" * 40)

    search_prompt = """
    Generate 5 search terms for finding stock videos related to 
    "sustainable technology and green energy solutions".
    Return only a JSON array of strings.
    """

    try:
        response = generate_response(search_prompt, provider=ModelProvider.REQUESTY)
        print("Generated Search Terms:")
        print(response)
    except Exception as e:
        print(f"❌ Error generating search terms: {str(e)}")

    # Example 3: Compare with OpenAI
    print("\n⚖️  Example 3: Comparing REQUESTY vs OpenAI responses")
    print("-" * 40)

    comparison_prompt = "Write a catchy title for a video about AI in healthcare."

    try:
        print("REQUESTY Response:")
        requesty_response = generate_response(
            comparison_prompt, provider=ModelProvider.REQUESTY
        )
        print(f"  {requesty_response}")

        print("\nOpenAI Response:")
        openai_response = generate_response(
            comparison_prompt, provider=ModelProvider.OPENAI
        )
        print(f"  {openai_response}")

    except Exception as e:
        print(f"❌ Error in comparison: {str(e)}")

    print("\n✨ Example completed!")


if __name__ == "__main__":
    asyncio.run(main())
