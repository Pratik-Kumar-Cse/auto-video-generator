import google.generativeai as genai
import time

# from .llm_call import get_image_info
from model_config import default_gemini_models
from config import settings

from ..utils import remove_file, download_image

genai.configure(api_key=settings.GEMINI_API_KEY)


safety_settings = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]


def text_call(prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)

    # Get the total tokens used and the cost of the call
    total_tokens = response.usage_metadata.total_token_count

    print("Total tokens used == >>", total_tokens)
    print(response.text)
    return response.text


def image_call(prompt, image_path, name="test"):

    sample_file = genai.upload_file(path=image_path, display_name=name)

    print(f"Uploaded file '{sample_file.display_name}' as: {sample_file.uri}")

    # Set the model to Gemini 1.5 Pro.
    model = genai.GenerativeModel(model_name=f"models/{default_gemini_models[0]}")

    response = model.generate_content([prompt, sample_file])

    genai.delete_file(sample_file.name)

    # Get the total tokens used and the cost of the call
    total_tokens = response.usage_metadata.total_token_count

    print("Total tokens used == >>", total_tokens)

    print(response.text)

    return response.text


def video_call(prompt, video_file_path):
    print("Uploading file...")
    video_file = genai.upload_file(path=video_file_path)
    try:

        # Prepare the file to be uploaded
        while video_file.state.name == "PROCESSING":
            print("Waiting for video to be processed.")
            time.sleep(10)
            video_file = genai.get_file(name=video_file.name)

        if video_file.state.name == "FAILED":
            raise ValueError(video_file.state.name)

        print("Video processing complete: " + video_file.uri)
        # Set the model to Gemini 1.5 Pro.
        model = genai.GenerativeModel(model_name=f"models/{default_gemini_models[0]}")

        # Make the LLM request.
        print("Making LLM inference request...")
        response = model.generate_content(
            [prompt, video_file],
            safety_settings=safety_settings,
        )

        print(response.text)
        data = response.text
        # Get the total tokens used and the cost of the call
        total_tokens = response.usage_metadata.total_token_count
        print("Total tokens used == >>", total_tokens)
        return data

    except Exception as e:
        genai.delete_file(video_file.name)
        print(f"Error video_call: {str(e)}")
        return None


def get_video_clips_details(script, video_path):
    return video_call(
        f"""
        Use this video file from which I need specific clip segments extracted.
        Your goal is:
            1. Read this new script: {script}, and analyze this script and find the relevant section with this video related visual and transcript.
            2. To compile a collection of short video clips (around 5-20 seconds each) that are relevant to visualize and spoken text the topics covered in my scripted narration.
            3. Fetch the accurate timestamp of the video clips the sub clips are total related to script.
            4. Remove the initial intro part more focus on features and good visual representation.
            5. Ensure that the total duration of the clips does not exceed the actual video duration, and that each clip's duration is accurate.
        For each main point in my script, please identify an applicable clip segment from the provided video file that illustrates or relates to that topic.
        Please provide the following details for each recommended clip:
            1. A brief and detailed description of the relevant script section
            2. The start and end time of the clip segment from the original video
            3. Any other context about why this clip is a good fit for that point in the script
        I will use these clips alongside the voiceover narration to create an edited video production.
        The clips should match and visualize the concepts I'm describing in the script.
        Please provide your recommendations in the following format:
            Clip 1
            Duration: (start_time in seconds, end_time in seconds)
            Description: [explain/description the about the section]

            Clip 2
            Duration: (start_time in seconds, end_time in seconds)
            Description: [explain/description the about the section]

        """,
        video_path,
    )


def get_reels_clips_details(script, video_path):
    return video_call(
        f"""
        Use this video file data from which I need specific clip segments extracted. 
        Your goal is:
        1. Read this new script: {script}, and analyze this script to find relevant sections that can be visually represented by clips from the provided video.
        2. Compile a collection of short video clips (around 10-15 seconds each) that are relevant to visualize the topics covered in my scripted narration.
        3. Fetch the accurate timestamps of the video clips, ensuring that the sub-clips are directly related to the script.
        4. Remove the initial intro part and focus more on features and good visual representations.
        5. Ensure that the total duration of the clips does not exceed the actual video duration, and that each clip's duration is accurate.

        For each main point in my script, please identify an applicable clip segment from the provided video file that illustrates or relates to that topic. 
        Please provide the following details for each recommended clip:
        1. A brief and detailed description of the relevant script section
        2. The start and end timestamps of the clip segment from the original video (in seconds) (mandatory)
        3. Any other context about why this clip is a good fit for that point in the script

        I will use these clips alongside the as background stock footage.
        The clips should match and visualize the concepts I'm describing in the script.

        Please provide your recommendations in the following format:
        Clip 1
        Duration: (start_time in seconds, end_time in seconds)
        Description: [explain/description the relevant section of the script]

        Clip 2
        Duration: (start_time in seconds, end_time in seconds)
        Description: [explain/description the relevant section of the script]
        ....

        """,
        video_path,
    )


def at_clip_in_video(video_script_with_timestamps):

    res = video_call(
        """
        Use this video file and Analyze the content and divide it into multiple sections based on the main topics covered.

        For each section, provide the following:
        1. Start and end times (in minutes:seconds format)
        2. A concise description summarizing the main topic of that section.
        3. These subsection I want to use in my new video so thing like a video editor.

        Please ensure that the sections are coherent and logically divided based on the changes in topic throughout the video.
        If possible, include timestamps that correspond to natural breaks or transitions in the content.
        The descriptions should be clear and accurately capture the essence of what is being discussed in each section."
        Please provide your recommendations in the following format:

        Clip 1
        Duration: (start_time in seconds, end_time in seconds)
        Description: [explain the about the section]

        Clip 2
        Duration: (start_time in seconds, end_time in seconds)
        Description: [explain the about the section]
        ...

        """,
        "../data/data.mp4",
    )

    prompt = f"""
        You are a video editor working on creating a new video by incorporating various video clips into a given video script. Your task is to analyze the script and the provided video clips, and then determine the most appropriate placement for clip within the script.

        You will be provided with the following information:

        1. The full video script text, which will be inserted in place of {video_script_with_timestamps} also have timestamp for reference for clip insert timing.
        2. A list of video clips, including their descriptions and timings, which will be inserted in place of {res}. 
        3. It is not necessary to add all clips in the script only add those clips that the related to script
        4. thing like these clips are the stock clips for a new video it and not mandate to insert all clips

        The format for clip will be:
        [Clip Number]
        [Clip Duration]:(start_time in seconds, end_time in seconds)
        [Clip Description]:

        Your goal is to analyze the script content and the provided video clips, and then recommend where clip should be inserted into the script to create a cohesive and well-structured final video. 
        Consider the context and flow of the script, as well as the relevance of clip's content to the script.

        Please provide your recommendations in the following format:

        Clip 1 Description: [description]
        Recommended Insertion Point: [timestamp or specific location in the script]
        Justification: [explain why this clip should be inserted at this point]

        Clip 2 Description: [description]
        Recommended Insertion Point: [timestamp or specific location in the script]
        Justification: [explain why this clip should be inserted at this point]

        ... (repeat for all provided clips)

        Please be as detailed and specific as possible in your recommendations and justifications, ensuring that the final video will flow smoothly and effectively convey the intended message.

        """
    res = text_call(prompt)
    return res


def get_images_details(
    video_id,
    script,
    images,
):

    details = []
    image_links = []
    image_number = 1
    for index, image in enumerate(images):
        if image_number == 7:
            break
        save_path = f"./temp/{video_id}/image_{image_number}.jpg"
        image_path = download_image(image, save_path)
        if image_path:
            try:
                prompt = """
                Analyze the provided image and perform image segmentation to identify the various elements and objects present. 
                Based on the results of the image segmentation, provide the following information:
                1. A brief description of the overall scene or contents of the image.
                2. A list of the main objects, elements, or regions identified through image segmentation, along with their approximate locations or positions within the image (e.g., top-left, center, bottom-right).
                3. An assessment of whether the image is relevant and suitable for visually representing or supporting the given script.

                In your response, please include the following sections with clear headings for better readability:
                [Image Number]
                {image_number}
                [Image Description]
                ...
                [Segmentation Results]
                ...

                video script is: {script}
                """
                # detail = get_image_info(prompt, image)
                detail = image_call(
                    prompt,
                    image_path,
                )
                details.append(detail)
                image_number = image_number + 1
                image_links.append(image)
            except Exception as err:
                print(f"[-] Error: {str(err)}")
                remove_file(image_path)
    print("details", details)
    return details, image_links


def check_video_match(script, video_path, search_term):

    prompt = f"""
        Analyze the provided video file and script for content matching and identify relevant timestamps:

        1. Script Analysis:
        - Review the provided script: {script}
        - Evaluate if the video content aligns with the script requirements
        - Identify specific timestamps where video segments match the script

        2. Visual Relevance Check:
        - Assess if the video's visual elements match the script's context
        - Check for appropriate setting, actions, and overall scene composition
        - Note any mismatches or inconsistencies

        3. Search Term Relevance Analysis:
        - Compare the video content against the search term: {search_term}
        - Identify specific time segments that match the search content
        - segments are relevant to visualize and voice text the topics covered in my scripted narration
        - For each relevant segment, provide:
            * Start and end timestamps in seconds
            * Relevance score for that segment (0 to 10, where 10 is most relevant)
            * Description of how the segment matches the search term
            * start_time and end_time should be in seconds as integers and with in the video timeframe.

        4. Overall Evaluation:
        - Assess the overall video quality and usability
        - If the video doesn't fully match the search intent, suggest alternative search terms
        - Provide recommendations for segment extraction if needed

        Expected Output Format:
        {{
            "relevance_score": 8,
            "relevant_segments": [
                {{
                    "start_time": 0,
                    "end_time": 30,
                    "segment_relevance_score": 8,
                    "segment_description": "Description of how this segment matches the search term"
                }}
            ],
            "alternative_search_terms": [
                "search term 1",
                "search term 2",
                "search term 3"
            ],
            "extraction_recommendations": "Specific recommendations for segment extraction and usage"
        }}

        Delivery Instructions:
        - Provide pure JSON response
        - No additional formatting, tags, or annotations
        - All timestamps must be in seconds as integers
        - Relevance scores must be integers between 0 and 10
        - Include all relevant segments, even if brief
        - Ensure clear, professional, and actionable insights
        """
    return video_call(
        prompt,
        video_path,
    )
