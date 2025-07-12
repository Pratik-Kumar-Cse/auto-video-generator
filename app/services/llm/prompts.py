from typing import List, Dict, Optional


def optimize_custom_prompt(custom_prompt: str) -> str:
    """
    Optimizes a custom prompt by adding essential elements while preserving its core message.

    Args:
        custom_prompt: The user-provided custom prompt

    Returns:
        str: Optimized version of the custom prompt
    """
    essential_elements = """
    Essential Elements to Include:
    - Clear hook and opening
    - Logical scene transitions
    - Visual descriptions
    - Engagement points
    - Natural pacing
    - Strong conclusion
    """

    structural_guidelines = """
    Structural Requirements:
    - Maintain natural flow
    - Include scene breaks
    - Balance information density
    - Use clear transitions
    - Support visual elements
    """

    # Remove any existing formatting instructions to prevent conflicts
    cleaned_prompt = custom_prompt.replace("Format:", "").replace("Formatting:", "")

    # Add optimization elements while preserving the original prompt
    optimized_prompt = f"""
    Original Custom Requirements:
    {cleaned_prompt}
    {essential_elements}
    {structural_guidelines}
    """

    return optimized_prompt


def build_script_prompt(
    topic: str,
    video_type,
    keywords,
    custom_prompt,
    language: str = "English",
) -> str:
    """
    Builds a detailed prompt for generating video scripts with specific parameters.
    Handles both custom and default prompts with optimization.

    Args:
        topic: Main subject of the video
        custom_prompt: Optional custom prompt to override default
        number_of_scenes: Number of distinct scenes/segments
        tone: Desired tone of the script
        target_duration: Approximate video length
        target_audience: Intended viewer demographic
        language: Script language

    Returns:
        str: Formatted prompt for script generation
    """

    if custom_prompt:
        # Optimize the custom prompt while preserving its intent
        base_prompt = optimize_custom_prompt(custom_prompt)
    else:
        base_prompt = f"""
        Generate a compelling {keywords.get("time")} video script about {topic} for a {keywords.get("audience")} audience in a {keywords.get("tone")} tone.

        Structure Guidelines:
        1. Hook (10-15 seconds):
        - Start with a powerful attention-grabbing statement or question
        - Create immediate emotional connection or curiosity
        - Use concrete examples or surprising statistics when relevant
        - Keep it concise and impactful

        2. Main Content (number_of_scenes based on {video_type}):
        - Break complex information into clear, digestible segments
        - Use smooth transitions between scenes
        - Include specific examples, data, or case studies
        - Address potential questions or counterpoints
        - Maintain a consistent narrative thread
        - Use descriptive language that creates clear mental images

        3. Visual Elements:
        - Describe key visuals needed for each scene
        - Suggest graphics, animations, or B-roll footage
        - Include pauses for important visual elements
        - Consider screen text for key points or data

        4. Engagement Elements:
        - Include rhetorical questions or thought-provoking statements
        - Add moments for viewer reflection
        - Use callbacks to earlier points for coherence
        - Incorporate storytelling elements when appropriate

        5. Pacing Guidelines:
        - Vary sentence length for dynamic delivery
        - Include natural pauses for emphasis
        - Mark points where visuals need time to register
        - Balance information density with clarity

        6. Closing (15-20 seconds):
        - Summarize key takeaways
        - End with a thought-provoking statement or call-to-action
        - Create a sense of completion while maintaining interest
        - Connect back to the opening hook
        """

    # Common parameters and requirements for both custom and default prompts
    technical_requirements = f"""
    Technical Requirements:
    - Write in {language}
    - Avoid technical jargon unless necessary for the topic
    - Use active voice and present tense
    - Format as plain text without markers (no "VOICEOVER:" or similar)
    - Include natural breaks between scenes
    - Target approximately {keywords.get("time")} of speaking time
    """

    content_requirements = """
    Content Requirements:
    - Focus on accuracy and credibility
    - Present information in a logical sequence
    - Balance depth with accessibility
    - Maintain engagement throughout
    - Avoid repetition unless for emphasis
    """

    # Add specific parameters to the prompt
    parameters = f"""
    Additional Parameters:
    Topic: {topic}
    Number of scenes: based on the video type is {video_type}
    Target duration: {keywords.get("time")}
    Tone: {keywords.get("tone")}
    Target audience: {keywords.get("audience")}
    Language: {language}
    Keywords: {keywords}
    """

    # Quality control checklist
    quality_checks = """
    Quality Requirements:
    - Ensure natural, conversational flow
    - Verify timing aligns with target duration
    - Confirm all technical terms are properly explained
    - Check for smooth transitions between scenes
    - Validate that the content matches the intended tone
    """

    # Combine all components
    return f"{base_prompt}\n\n{technical_requirements}\n\n{content_requirements}\n\n{parameters}\n\n{quality_checks}"


def build_search_terms_prompt(video_subject: str, amount: int, script: str) -> str:
    # Implementation of search terms prompt building
    # Build prompt
    prompt = f"""
    Generating relevant {amount} search terms for youtube video keywords based on a given script.
    Follow these instructions carefully:

    1. Divide the script into distinct sections or scenes.
    2. For each section, generate 3-5 search terms that directly relate to the content of that section or scenes and would be suitable for finding relevant stock footage.
    3. Ensure the search terms are in the correct sequence, following the order of the script sections.
    4. Return the search terms as a JSON array of strings, with each string representing one search terms.
    5. Do not include any additional text or explanations. Only return the JSON array.
    6. Return Only amount {amount} of search terms
    YOU MUST ONLY RETURN THE JSON-ARRAY OF STRINGS.
    YOU MUST NOT RETURN ANYTHING ELSE.
    YOU MUST NOT RETURN THE SCRIPT.
    REMOVE this remove ```json ``` this we don't want in response
    Example JSON array:
    ["search term 1", "search term 2", "title for section 3", ...]
    Script: {script}
    """

    return prompt


def build_shorts_title_prompt(script: str) -> str:
    # Implementation of title prompt building
    # Build prompt for title
    title_prompt = f"""
    Create an attention-grabbing, SEO-optimized title for a YouTube Shorts video using video script.
    take reference from video script The video script is: {script}

    Your title should:
    1. Be concise (20-50 characters long)
    2. Include relevant keywords
    3. Spark curiosity or emotion
    4. Accurately reflect the video content
    5. Avoid clickbait tactics
    6. Add two hashtags that the related to the video

    Return only the title, without any additional formatting or explanation.
    """
    return title_prompt


def build_video_title_prompt(script: str) -> str:
    title_prompt = f"""
    Generate a catchy and SEO-friendly title for a YouTube video based on the following script:

    {script}

    Guidelines for the title:
    1. Keep it concise, ideally under 60 characters.
    2. Make it attention-grabbing and clickable.
    3. Include key topics or themes from the script.
    4. Use power words to increase engagement.
    5. Consider using numbers or questions if appropriate.
    6. Ensure it accurately reflects the video content.
    7. Optimize for search engines without keyword stuffing.
    8. Avoid clickbait - the title should genuinely represent the content.
    9. Add two hashtags that the related to the video

    Return only the title as a plain string, without any additional formatting or labels like "Title:".
    """
    return title_prompt.strip()


def build_shorts_description_prompt(
    script: str,
    website: Optional[str] = None,
    social_media: Optional[Dict[str, str]] = None,
) -> str:
    # Implementation of description prompt building
    description_prompt = f"""
    INPUT:
    video_script: {script}

    Create a captivating YouTube shorts video description using script.
    Follow this structure:

    1. Write an intriguing opening line to hook viewers (without tags).
    2. Summarize these key points from the script in 1 short paragraph:
    • Key point 1
    • Key point 2
    • Key point 3
    3. Include a call-to-action for likes, comments, and subscriptions (without tags).

    After the main description, include these sections (take script as context):
    
    """

    if website:
        description_prompt += f"""
    🌐 Visit our website: {website}
    """

    if social_media:
        description_prompt += """
    [SOCIAL MEDIA]
    """
        for platform, link in social_media.items():
            emoji = get_social_media_emoji(platform)
            description_prompt += f"{emoji} {platform.capitalize()}: {link}\n"

    description_prompt += """
    
    [HASHTAGS]
    Add some hashtags that are totally related to the content

    👉 Customize this call-to-action based on your content and goals.

    🔔 New content regularly! Follow/subscribe and enable notifications to stay updated.

    Instructions:
    1. Format the description exactly as shown, using emojis, capital letters for section headers in square brackets, and appropriate line breaks.
    2. Adjust timestamps and key points based on the video's actual content using the script that have timestamp.
    3. Add 1-3 more hashtags according to the script in the [HASHTAGS] section.
    4. Ensure the main description (before the sections) is concise and engaging.
    5. Tailor the call-to-action to the specific video content while encouraging engagement.
    """

    return description_prompt


def get_social_media_emoji(platform: str) -> str:
    emoji_map = {
        "facebook": "📘",
        "instagram": "📷",
        "x": "🐦",
        "linkedin": "💼",
        "medium": "✍️",
        "youtube": "🎥",
        "tiktok": "🎵",
    }
    return emoji_map.get(platform.lower(), "🔗")


def build_video_description_prompt(
    script: str,
    website: Optional[str] = None,
    social_media: Optional[Dict[str, str]] = None,
) -> str:
    # Implementation of description prompt building
    description_prompt = f"""
    INPUT:
    video_script with timestamps: {script}

    Create a captivating YouTube video description using script.
    Follow this structure:

    1. Write an intriguing opening line to hook viewers (without tags).
    2. Summarize these key points from the script in 1 short paragraph:
    • Key point 1
    • Key point 2
    • Key point 3
    3. Include a call-to-action for likes, comments, and subscriptions (without tags).

    After the main description, include these sections (take script as context):

    """
    if website:
        description_prompt += f"""
    🌐 Visit our website: {website}
    """

    if social_media:
        description_prompt += """
    [SOCIAL MEDIA]
    """
        for platform, link in social_media.items():
            emoji = get_social_media_emoji(platform)
            description_prompt += f"{emoji} {platform.capitalize()}: {link}\n"

    description_prompt += """

    Chapters
    Add timestamps that help to divide the video in sections take response from video_script with timestamps.
    
    example like:
        Chapters
        00:00 Introduction
        00:15 {{Key Point 1}}
        00:30 {{Key Point 2}}
        00:45 {{Key Point 3}}
        ...
        01:00 Conclusion

    [HASHTAGS]
    Add some hashtags that are totally related to the content

    👉 Customize this call-to-action based on your content and goals.

    🔔 New content regularly! Follow/subscribe and enable notifications to stay updated.

    Instructions:
    1. Format the description exactly as shown, using emojis, capital letters for section headers in square brackets, and appropriate line breaks.
    2. Adjust timestamps and key points based on the video's actual content using the script that have timestamp.
    3. Add 1-3 more hashtags according to the script in the [HASHTAGS] section.
    4. Ensure the main description (before the sections) is concise and engaging.
    5. Tailor the call-to-action to the specific video content while encouraging engagement.
    """

    return description_prompt


# def build_video_title_prompt(script: str) -> str:
#     title_prompt = f"""
#     Generate a catchy and SEO-friendly title for a YouTube video based on the following script:

#     {script}

#     Guidelines for the title:
#     1. Keep it concise, ideally under 60 characters.
#     2. Make it attention-grabbing and clickable.
#     3. Include key topics or themes from the script.
#     4. Use power words to increase engagement.
#     5. Consider using numbers or questions if appropriate.
#     6. Ensure it accurately reflects the video content.
#     7. Optimize for search engines without keyword stuffing.
#     8. Avoid clickbait - the title should genuinely represent the content.

#     Return only the title as a plain string, without any additional formatting or labels like "Title:".
#     """
#     return title_prompt.strip()


# def build_shorts_description_prompt(script: str) -> str:
#     # Implementation of description prompt building
#     description_prompt = f"""
#     INPUT:
#     video_script: {script}

#     Create a captivating YouTube shorts video description using script.
#     Follow this structure:

#     1. Write an intriguing opening line to hook viewers (without tags).
#     2. Summarize these key points from the script in 1 short paragraph:
#     • Key point 1
#     • Key point 2
#     • Key point 3
#     3. Include a call-to-action for likes, comments, and subscriptions (without tags).
#     4. Add #RapidInnovation hashtag.

#     After the main description, include these sections (take script as context):

#     🔗 Rapid Innovation Website: https://www.rapidinnovation.io/
#     🔗 Our Portfolio: https://www.rapidinnovation.io/portfolio

#     [SOCIAL MEDIA]
#     📘 Facebook: https://www.facebook.com/rapidinnovation.io/
#     📷 Instagram: https://www.instagram.com/rapidinnovation.io/
#     🐦 Twitter: https://x.com/InnovationRapid
#     💼 LinkedIn: https://www.linkedin.com/company/rapid-innovation/mycompany/
#     ✍️ Medium: https://bit.ly/RapidInnovationMedium

#     📧 Email: hello@rapidinnovation.io
#     🌐 Website: https://www.rapidinnovation.io/

#     [HASHTAGS]
#     #RapidInnovation #AI #Innovation {{additional_hashtags}}

#     👉 Ready to revolutionize your business with AI automation? Contact Rapid Innovation for cutting-edge solutions!

#     🎥 New videos every week! Subscribe and hit the notification bell to stay updated.

#     ©️ 2024 Rapid Innovation. All rights reserved.

#     Instructions:
#     1. Format the description exactly as shown, using emojis, capital letters for section headers in square brackets, and appropriate line breaks.
#     2. Adjust timestamps and key points based on the video's actual content using the script that have timestamp.
#     3. Add 1-3 more hashtags according to the script in the [HASHTAGS] section.
#     4. Ensure the main description (before the sections) is concise and engaging.
#     5. Tailor the call-to-action to the specific video content while encouraging engagement.
#     """

#     return description_prompt


# def build_video_description_prompt(script: str) -> str:
#     # Implementation of description prompt building
#     description_prompt = f"""
#     INPUT:
#     video_script with timestamps: {script}

#     Create a captivating YouTube video description using script.
#     Follow this structure:

#     1. Write an intriguing opening line to hook viewers (without tags).
#     2. Summarize these key points from the script in 1 short paragraph:
#     • Key point 1
#     • Key point 2
#     • Key point 3
#     3. Include a call-to-action for likes, comments, and subscriptions (without tags).
#     4. Add #RapidInnovation hashtag.

#     After the main description, include these sections (take script as context):

#     🔗 Rapid Innovation Website: https://www.rapidinnovation.io/
#     🔗 Our Portfolio: https://www.rapidinnovation.io/portfolio

#     [SOCIAL MEDIA]
#     📘 Facebook: https://www.facebook.com/rapidinnovation.io/
#     📷 Instagram: https://www.instagram.com/rapidinnovation.io/
#     🐦 Twitter: https://x.com/InnovationRapid
#     💼 LinkedIn: https://www.linkedin.com/company/rapid-innovation/mycompany/
#     ✍️ Medium: https://bit.ly/RapidInnovationMedium

#     📧 Email: hello@rapidinnovation.io
#     🌐 Website: https://www.rapidinnovation.io/

#     [TIMESTAMPS]
#     00:00 - Introduction
#     00:15 - {{Key Point 1}}
#     00:30 - {{Key Point 2}}
#     00:45 - {{Key Point 3}}
#     01:00 - Conclusion

#     [HASHTAGS]
#     #RapidInnovation #AI #Innovation {{additional_hashtags}}

#     👉 Ready to revolutionize your business with AI automation? Contact Rapid Innovation for cutting-edge solutions!

#     🎥 New videos every week! Subscribe and hit the notification bell to stay updated.

#     ©️ 2024 Rapid Innovation. All rights reserved.

#     Instructions:
#     1. Format the description exactly as shown, using emojis, capital letters for section headers in square brackets, and appropriate line breaks.
#     2. Adjust timestamps and key points based on the video's actual content using the script that have timestamp.
#     3. Add 1-3 more hashtags according to the script in the [HASHTAGS] section.
#     4. Ensure the main description (before the sections) is concise and engaging.
#     5. Tailor the call-to-action to the specific video content while encouraging engagement.
#     """

#     return description_prompt


def build_reel_captions_prompt(subject: str, script: str) -> str:
    # Implementation of reel captions prompt building
    prompt = f"""
    You are an expert social media copywriter tasked with creating engaging captions for Instagram reels. 
    Your goal is to craft captions that are attention-grabbing, relevant, and encourage viewers to watch the reel.
    You will be provided with the following information:
    1. The subject or theme of the reel (e.g., Tech, Science, Marketing etc.)
    2. A brief script or summary of the reel's content

    Using this information, you should generate a compelling caption that:

    - Hooks the viewer's interest from the beginning
    - Provides context or a teaser about the reel's content
    - Incorporates relevant hashtags and emojis
    - Keeps the caption concise (around 1-2 sentences)
    - Maintains a tone and voice appropriate for the subject matter

    The caption should be written in a way that entices viewers to watch the reel and engage with the content. Remember to focus on creating a catchy, attention-grabbing caption that accurately represents the reel's theme and content.

    Subject/Theme: {subject}
    Reel Script/Summary: {script}

    Please generate an Instagram reel caption based on the provided information.
    """

    return prompt


# def build_script_text_prompt(script: str) -> str:
#     # Implementation of script text prompt building
#     prompt = f"""
#     Please provide a clean version of the following video script:

#     {script}
#     Instructions:
#     1. Remove all HTML tags, XML tags, or any other markup languages.
#     2. Omit any headings or titles.
#     3. Exclude bullet points or numbered lists.
#     4. Preserve the main content of the script, including paragraphs and line breaks.
#     5. Maintain the original order and flow of the content.
#     6. Exclude these type of tags: **Host:**, Narrator:,**Narrator (V.O.):**,
#     7. Also don't add these type of lines eg **[Opening Shot: Quick visual montage of the Hummer EV zooming over various terrains, cityscapes, and off-road vistas.]**

#     Return only the plain text of the script without any formatting or structural elements."""

#     return prompt


def build_script_text_prompt(script: str) -> str:
    """
    Generate a comprehensive prompt for extracting clean, verbatim text from a video script.

    This function creates a detailed prompt that guides text extraction by specifying
    precise rules for processing video script content, ensuring only the essential
    spoken text is retained.

    Args:
        script (str): The original video script text to be processed.

    Returns:
        str: A carefully crafted prompt with explicit instructions for text extraction.
    """
    prompt = f"""
    Extract Video Script Text
    Context:
    You are a precise text extraction assistant tasked with converting a raw video script 
    into a clean, coherent text representation.

    Source Script:
    {script}

    Extraction Guidelines:
    -------------------
    1. Content Preservation:
    - Capture only spoken dialogue and direct quotes
    - Maintain original sequence and narrative flow
    - Preserve speaker's exact wording and punctuation

    2. Content Filtering:
    - Completely remove:
        * Scene descriptions
        * Stage directions
        * Formatting markers (**, [], XML/HTML tags)
        * Technical screenplay annotations
    
    3. Text Refinement:
    - Remove speaker labels (e.g., **Narrator:**, **Host:**)
    - Eliminate square bracket annotations
    - Strip unnecessary whitespaces
    - Retain natural speech patterns, including ellipses

    4. Output Specifications:
    - Generate a continuous, uninterrupted text stream
    - Ensure readability and coherence
    - No additional formatting or structural elements

    Desired Output:
    --------------
    A pure, unembellished text representation of the script's spoken content, 
    reflecting the original narrative essence.

    Proceed with meticulous text extraction."""

    return prompt


def build_divide_script_prompt(script: str) -> str:
    # Implementation of divide script prompt building
    prompt = f"""
        You are the Scene_Creator, an AI agent responsible for processing video scripts and dividing them into distinct scenes.
        Your primary tasks:
        1. Carefully analyze the provided video script.
        2. Remove all HTML tags, XML tags, or any other markup languages.
        3. Omit any headings or titles.
        4. Exclude bullet points or numbered lists.
        5. Divide the script into logical scenes based on:
        - Content shifts
        - Theme changes
        - Narrative progression
        - Setting changes
        - Time jumps or transitions
        6. Present each scene's content verbatim from the original script.
        7. Generate 2 relevant search terms for each scene, suitable for finding appropriate stock footage.
        8. Maintain the correct sequence of scenes and search terms as they appear in the original script.
        
        Inputs:
        script: {script}

        Returns:
        list: A list of dictionaries, where each dictionary represents a scene with its content and search terms.
        don't include ```python just return in this format
        {
            [
                {
                    "scene": "Exact content of Scene 1...",
                    "search_terms": ["Term 1", "Term 2", "Term 3"]
                },
                {
                    "scene": "Exact content of Scene 2...",
                    "search_terms": ["Term 1", "Term 2", "Term 3", "Term 4"]
                },
                ...
            ]
        }

        Guidelines:
        - Preserve the original script's exact wording, formatting, and style in each scene.
        - Ensure logical scene divisions that maintain the narrative flow.
        - Do not add scene numbers, labels, or any extra information not present in the original script.
        - Generate concise, relevant search terms that accurately reflect each scene's content.
        - Avoid summarizing or modifying the script content in any way.
    """

    return prompt


def build_intro_placement_prompt(script_with_subtitle: str) -> str:
    prompt = f"""
    Analyze the provided video script with subtitles and timestamps to determine the optimal placement for an intro video. Follow these guidelines:

    1. Identify the best timestamp for intro placement, considering:
       - It should appear after any initial greetings or brief opening remarks.
       - It must precede the main content.
       - The placement should feel natural and not disrupt the script's flow.
    2. Ensure the intro is positioned in the initial phase of the main content.
    3. Verify that the chosen location directly relates to the script's content.
    4. Avoid inserting the intro mid-sentence or interrupting a complete thought.
    5. Consider the viewer's engagement:
       - The intro should appear early enough to set the tone.
       - It shouldn't be so late that viewers lose interest.
    6. Pay attention to natural pauses or transitions in the script.
    7. If applicable, place the intro after a "hook" that captures viewer attention.

    Video script with subtitles and timestamps (in seconds):
    {script_with_subtitle}

    IMPORTANT: Your response must be ONLY a single float number representing the optimal timestamp in seconds (e.g., 4.5, 10.75, etc.). Do not include any explanations or additional text.
    """

    return prompt


# Helper methods for cleaning and parsing responses
def clean_script(response: str, paragraph_number: int) -> str:
    # Implementation of script cleaning
    pass


def parse_search_terms(response: str) -> List[str]:
    # Implementation of search terms parsing
    pass
