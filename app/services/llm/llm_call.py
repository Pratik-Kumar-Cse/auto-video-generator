import re
import json
import logging
import openai
# import google.generativeai as genai
# import anthropic
from openai import OpenAI

from app.constant.enum.model_enum import ModelProvider
from typing import Tuple, List
from model_config import (
    default_openai_model,
    default_requesty_model,
    default_claude_model,
    default_deepseek_model,
    default_gemini_model,
)
from app.core.config import settings

# Initialize logger
logger = logging.getLogger(__name__)


from .prompts import (
    build_script_prompt,
    build_search_terms_prompt,
    build_video_title_prompt,
    build_video_description_prompt,
    build_reel_captions_prompt,
    build_script_text_prompt,
    build_divide_script_prompt,
    build_intro_placement_prompt,
    build_shorts_title_prompt,
    build_shorts_description_prompt,
)


def generate_image(prompt):
    response = openai.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    return image_url


def get_image_info(prompt, image_url):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    token_used = response.usage.total_tokens

    print("token_used ===>>", token_used)

    response = response.choices[0].message.content

    return response


def generate_response(
    prompt: str,
    provider=ModelProvider.OPENAI,
) -> str:
    """
    Generate a response using the specified AI provider.
    Args:
        prompt (str): The input prompt for the AI model.
        provider: The AI provider to use.
    Returns:
        str: The response from the AI model.
    """
    logger.info(f"Generating response using provider: {provider.value}")
    logger.debug(f"Prompt length: {len(prompt)} characters")
    
    try:
        if provider == ModelProvider.OPENAI:
            logger.info(f"Using OpenAI model: {default_openai_model}")
            openai.api_key = settings.OPENAI_API_KEY
            response = openai.chat.completions.create(
                model=default_openai_model,
                messages=[{"role": "user", "content": prompt}],
            )
            token_used = response.usage.total_tokens
            logger.info(f"OpenAI tokens used: {token_used}")
            response = response.choices[0].message.content
            
        elif provider == ModelProvider.REQUESTY:
            logger.info(f"Using REQUESTY model: {default_requesty_model}")
            # Use OpenAI-compatible client for Requesty API
            client = OpenAI(
                api_key=settings.REQUESTY_KEY,
                base_url="https://api.requesty.com/v1"
            )
            response = client.chat.completions.create(
                model=default_requesty_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7,
            )
            token_used = response.usage.total_tokens
            logger.info(f"REQUESTY tokens used: {token_used}")
            response = response.choices[0].message.content
        elif provider == ModelProvider.GOOGLE:
            logger.info(f"Using Google Gemini model: {default_gemini_model}")
            # genai.configure(api_key=settings.GEMINI_API_KEY)
            # model = genai.GenerativeModel(default_gemini_model)
            # response_model = model.generate_content(prompt)
            # token_used = response_model.usage_metadata.total_token_count
            # logger.info(f"Google tokens used: {token_used}")
            # response = response_model.text
            logger.warning("Google Gemini provider not implemented yet")
            raise NotImplementedError("Google Gemini provider not implemented")
            
        elif provider == ModelProvider.DEEPSEEK:
            logger.info(f"Using DeepSeek model: {default_deepseek_model}")
            # Backward compatibility with https://api.deepseek.com/v1
            client = OpenAI(
                api_key=settings.DEEPSEEK_API,
                base_url="https://api.deepseek.com"
            )
            response = client.chat.completions.create(
                model=default_deepseek_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant"
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1024,
                temperature=0.7,
                stream=False,
            )
            if hasattr(response, 'usage') and response.usage:
                logger.info(
                    f"DeepSeek tokens used: {response.usage.total_tokens}"
                )
            response = response.choices[0].message.content
            
        elif provider == ModelProvider.ANTHROPIC:
            logger.info(f"Using Anthropic Claude model: {default_claude_model}")
            # client = anthropic.Anthropic(api_key=settings.CLAUDE_KEY)
            # message = client.messages.create(
            #     model=default_claude_model,
            #     max_tokens=1024,
            #     messages=[{"role": "user", "content": prompt}],
            # )
            # response = message.content
            logger.warning("Anthropic Claude provider not implemented yet")
            raise NotImplementedError("Anthropic Claude provider not implemented")
        else:
            logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
            
        logger.info("Response generated successfully")
        logger.debug(f"Response length: {len(response)} characters")
        return response
        
    except Exception as e:
        logger.error(f"Error generating response with {provider.value}: {str(e)}")
        raise


def generate_ai_script(
    topic: str,
    video_type,
    keywords,
    custom_prompt=None,
) -> str:
    """
    Generate a script for a video, depending on the subject of the video, the number of paragraphs, and the AI model.

    Args:

        video_subject (str): The subject of the video.

        paragraph_number (int): The number of paragraphs to generate.

    Returns:

        str: The script for the video.

    """

    # Build prompt

    prompt = build_script_prompt(
        topic,
        video_type,
        keywords,
        custom_prompt,
    )

    # Generate script
    response = generate_response(prompt)

    # Return the generated script
    if response:
        # Clean the script
        # Remove asterisks, hashes
        response = response.replace("*", "")
        response = response.replace("#", "")

        # Remove markdown syntax
        response = re.sub(r"\[.*\]", "", response)
        response = re.sub(r"\(.*\)", "", response)

        # Split the script into paragraphs
        paragraphs = response.split("\n\n")

        # Join the selected paragraphs into a single string
        final_script = "\n\n".join(paragraphs)

        # Print to console the number of paragraphs used
        print(colored(f"Number of paragraphs used: {len(paragraphs)}", "green"))

        return final_script
    else:
        print(colored("[-] GPT returned an empty response.", "red"))
        return None


def get_search_terms(
    video_subject: str,
    amount: int,
    script: str,
) -> List[str]:
    """
    Generate a JSON-Array of search terms for stock videos,
    depending on the subject of a video.

    Args:
        video_subject (str): The subject of the video.
        amount (int): The amount of search terms to generate.
        script (str): The script of the video.

    Returns:
        List[str]: The search terms for the video subject.
    """

    # Build prompt
    prompt = build_search_terms_prompt(video_subject, amount, script)

    # Generate search terms
    response = generate_response(prompt)

    # Parse response into a list of search terms
    search_terms = []

    try:
        search_terms = json.loads(response)
        if not isinstance(search_terms, list) or not all(
            isinstance(term, str) for term in search_terms
        ):
            raise ValueError("Response is not a list of strings.")

    except (json.JSONDecodeError, ValueError):
        # Get everything between the first and last square brackets
        response = response[response.find("[") + 1 : response.rfind("]")]

        print(
            colored(
                "[*] GPT returned an unformatted response. Attempting to clean...",
                "yellow",
            )
        )

        # Attempt to extract list-like string and convert to list
        match = re.search(r'\["(?:[^"\\]|\\.)*"(?:,\s*"[^"\\]*")*\]', response)
        print(match.group())
        if match:
            try:
                search_terms = json.loads(match.group())
            except json.JSONDecodeError:
                print(colored("[-] Could not parse response.", "red"))
                return []

    # Let user know
    print(
        colored(
            f"\nGenerated {len(search_terms)} search terms: {', '.join(search_terms)}",
            "cyan",
        )
    )

    # Return search terms
    return search_terms


def generate_metadata(
    video_subject: str, script: str, video_type="Video"
) -> Tuple[str, str, List[str]]:
    """
    Generate metadata for a YouTube video, including the title, description, and keywords.

    Args:
        video_subject (str): The subject of the video.
        script (str): The script of the video.

    Returns:
        Tuple[str, str, List[str]]: The title, description, and keywords for the video.
    """
    if video_type == "Video":
        # Build prompt for title
        title_prompt = build_video_title_prompt(script)
        description_prompt = build_video_description_prompt(script)
    else:
        # Build prompt for title
        title_prompt = build_shorts_title_prompt(
            script,
        )
        description_prompt = build_shorts_description_prompt(script)

    # Generate title
    title = generate_response(title_prompt).strip()

    # Generate description
    description = generate_response(description_prompt).strip()

    # Generate keywords
    keywords = get_search_terms(video_subject, 5, script)

    return title, description, keywords


def generate_similar_search_terms(input_text, num_terms=5):
    """
    Generate similar search terms for finding stock videos based on the given input text.

    Args:
        input_text (str): The input text describing the desired stock video.
        num_terms (int, optional): The number of similar search terms to generate. Default is 5.

    Returns:
        list: A list of similar search terms.
    """
    prompt = f"Generate {num_terms} similar search terms that help to finding stock videos related to the following text: \n\n{input_text} , don't need stock videos keyword remove it. YOU MUST ONLY RETURN THE JSON-ARRAY OF STRINGS. "

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7,
    )

    return json.loads(response.choices[0].message.content)


def generate_reel_captions(subject, script):
    prompt = build_reel_captions_prompt(subject, script)
    return generate_response(prompt).strip()


def get_title(script):

    prompt = f"""
    Your task to write the title (5-10) words of the video using the video script.
    video Script is: {script}
    """

    return generate_response(prompt).strip()


def get_script_text(script):
    prompt = build_script_text_prompt(script)
    return generate_response(prompt).strip()


def divide_and_get_search_terms(script):
    prompt = build_divide_script_prompt(script)
    return generate_response(prompt).strip()


def get_intro_placement_time(script_with_subtitle):

    prompt = build_intro_placement_prompt(script_with_subtitle)

    return generate_response(prompt).strip()


def get_article_summary(data):

    prompt = f"""
    Provide a concise summary of the following article:

    Content:
    {data}

    Please adhere to these guidelines:
    1. Capture the main ideas and key points of the article.
    2. Maintain a neutral tone.
    3. Keep the summary to in more details in more then 200 words. and Keep in paragraphs
    4. Do not include any personal opinions or additional information not present in the original text.
    5. Use clear and simple language.

    Return the summary in plain text format.
    """
    return generate_response(prompt).strip()


def generate_prompt(script):
    prompt = f"""
    Based on the following YouTube video script, create a detailed and compelling prompt for an AI image generator to produce an eye-catching thumbnail image:

    VIDEO SCRIPT:
    {script}

    Please generate an image prompt that includes:

    1. Main Subject: Identify and describe the central focus of the video.
    2. Action or State: Explain what the main subject is doing or how it appears.
    3. Keep the left side of the image dark and faded, while the right side showcases and add approx 20 chars video summary at left hand side in big text.
    4. Background: Describe the setting or context that best represents the video's content.
    5. Color Scheme: Propose a color palette that captures the video's mood and enhances visibility.
    6. Composition: Describe the layout, ensuring it's optimized for a YouTube thumbnail (16:9 aspect ratio).
    7. Technical Specifications: Mention "high resolution" and "16:9 aspect ratio" for YouTube compatibility.
    8. Unique Element: Add one distinctive feature that will make the thumbnail stand out.

    Combine these elements into a coherent, detailed prompt of 3-4 sentences that an AI image generation tool could use to create a compelling YouTube thumbnail image. 
    The prompt should be clear, specific, and designed to produce an image that accurately represents the video content while being visually striking and attention-grabbing.
    """
    return generate_response(prompt).strip()


def get_image_search_topic(topic):
    prompt = f"""
    Provide concise search terms for the following topic/content to help find relevant images:
    Topic: {topic}
    Return the search terms in plain text format give at most 3 search terms.
    """
    return generate_response(prompt).strip()
