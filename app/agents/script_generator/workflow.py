import asyncio

from app.agents.script_generator.agents import (
    Master_Agent,
    create_video_team,
    create_analysis_team,
    create_article_analysis_team,
    create_script_analysis_team,
    create_reel_team,
    create_reel_analysis_team,
    create_reel_article_analysis_team,
    create_reel_script_analysis_team,
    search_tool,
)
from app.constant.enum.video_enum import VideoType
from autogen_agentchat.messages import TextMessage
from app.loggers.logger import get_logger

logger = get_logger(__name__)


# Mock ScriptLogger for testing
class ScriptLogger:
    """Mock implementation for ScriptLogger."""

    def __init__(self):
        pass

    def log(self, message):
        print(f"LOG: {message}")


# Mock implementations for missing services
def save_video(video_link):
    """Mock implementation for save_video."""
    return f"mock_path_for_{video_link}"


def extract_article(link):
    """Mock implementation for extract_article."""
    return f"Mock article content from {link}"


def extract_pdf_content_from_url(link):
    """Mock implementation for extract_pdf_content_from_url."""
    return f"Mock PDF content from {link}"


def get_transcription_from_yt_video(link):
    """Mock implementation for get_transcription_from_yt_video."""
    return f"Mock video title for {link}", f"Mock transcript for {link}"


class ScriptWorkFlow:

    def __init__(self):
        logger.info("ScriptWorkFlow initialized")

    async def script_using_video(
        self, topic, video_type, keywords, link=None, video_link=None
    ):
        """Generate script using video content."""
        logger.info(
            f"Generating script from video: topic='{topic}', "
            f"type={video_type}, has_link={bool(link or video_link)}"
        )

        if video_link:
            logger.debug(f"Processing uploaded video: {video_link}")
            save_video(video_link)
            # video_transcript = process_file(path)
            video_transcript = "Video content processed"  # Placeholder
        else:
            logger.debug(f"Processing YouTube video: {link}")
            video_title, video_transcript = get_transcription_from_yt_video(link)
            if not video_transcript:
                logger.warning("No transcript found, using search tool")
                video_transcript = search_tool(video_title or topic)

        task = f"""
            topic is: {topic} and video_transcript is: {video_transcript}
            keywords is : {keywords} use these keyword as reference to
            generate script where
                Time: This likely refers to the duration or length of the
                script.
                Objective: This describes the main goal or purpose of the
                script.
                Audience: This specifies who the script is intended for.
                Gender: This might refer to the gender of the target audience
                or the gender of the characters/speakers in the script.
                Tone: This describes the overall mood or attitude of the
                script.
                Speakers: This likely refers to the characters in the script.
            """

        return await self.generate_script_using_video(task, video_type)

    async def script_using_blog(self, topic, video_type, keywords, link):
        """Generate script using blog/article content."""

        if link.endswith(".pdf"):
            content = extract_pdf_content_from_url(link)
        else:
            content = extract_article(link)

        task = f"""topic is: {topic} and article content : {content}.
        keywords is : {keywords} use these keyword as reference to
        generate script where
            Time: This likely refers to the duration or length of the script.
            Objective: This describes the main goal or purpose of the script.
            Audience: This specifies who the script is intended for.
            Gender: This might refer to the gender of the target audience
            or the gender of the characters/speakers in the script.
            Tone: This describes the overall mood or attitude of the script.
            Speakers: This likely refers to the characters in the script.
        """

        return await self.generate_script_using_article(task, video_type)

    async def script_using_script(self, topic, video_type, keywords):
        """Generate script using existing script data."""

        task = f"""this is the topic or script data with instructions: {topic}.
        keywords is : {keywords} use these keyword as reference to
        generate script where
            Time: This likely refers to the duration or length of the script.
            Objective: This describes the main goal or purpose of the script.
            Audience: This specifies who the script is intended for.
            Gender: This might refer to the gender of the target audience
            or the gender of the characters/speakers in the script.
            Tone: This describes the overall mood or attitude of the script.
            Speakers: This likely refers to the characters in the script.
            """
        return await self.generate_script_using_data(task, video_type)

    async def script_using_topic(self, topic, video_type, keywords):
        """Generate script using topic."""

        task = f"""topic is: {topic}.
        keywords is : {keywords} use these keyword as reference to
        generate script where
            Time: This likely refers to the duration or length of the script.
            Objective: This describes the main goal or purpose of the script.
            Audience: This specifies who the script is intended for.
            Gender: This might refer to the gender of the target audience
            or the gender of the characters/speakers in the script.
            Tone: This describes the overall mood or attitude of the script.
            Speakers: This likely refers to the characters in the script.
        """
        return await self.generate_script_using_topic(task, video_type)

    async def script_from_latest_news(self, video_type, keywords):
        """Generate script from latest news."""

        task = f"""
        Topic: Last week, latest trends groundbreaking news and
        technologies emerged in the AI, Blockchain.
        keywords : {keywords} as reference to generate script where
            Time: This likely refers to the duration or length of the script.
            Objective: This describes the main goal or purpose of the script.
            Audience: This specifies who the script is intended for.
            Gender: This might refer to the gender of the target audience
            or the gender of the characters/speakers in the script.
            Tone: This describes the overall mood or attitude of the script.
            Speakers: This likely refers to the characters in the script.
            """
        return await self.generate_script_from_latest_news(task, video_type)

    async def generate_script_contents(self, script):
        """Generate script content with scenes."""

        task = f"""
            create script scene with hook, flow, engagement and trend for
            this script. script is: {script}
        """

        # Use a simple team for content generation
        team = create_video_team()
        result = await team.run(task=task)
        return self._extract_final_message(result)

    async def _run_master_agent(self, topic: str) -> str:
        """Run Master_Agent to determine video type."""
        try:
            # Create a simple message for the master agent
            message = TextMessage(content=topic, source="user")
            response = await Master_Agent.on_messages(
                [message], cancellation_token=None
            )
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Master agent error: {e}", exc_info=True)
            return "It is a video."

    async def generate_script_using_video(self, task, video_type):
        """Generate script using video analysis workflow."""

        if video_type == VideoType.LONG.value:
            team = create_analysis_team()
        else:
            team = create_reel_analysis_team()

        try:
            result = await team.run(task=task)
            return self._extract_final_message(result)
        except Exception as e:
            logger.error(f"Error in generate_script_using_video: {e}", exc_info=True)
            return f"Error generating script: {str(e)}"

    async def generate_script_using_article(self, task, video_type):
        """Generate script using article analysis workflow."""

        if video_type == VideoType.LONG.value:
            team = create_article_analysis_team()
        else:
            team = create_reel_article_analysis_team()

        try:
            result = await team.run(task=task)
            return self._extract_final_message(result)
        except Exception as e:
            logger.error(
                f"Error in generate_script_using_article: {e}", exc_info=True
            )
            return f"Error generating script: {str(e)}"

    async def generate_script_using_data(self, task, video_type):
        """Generate script using script data analysis workflow."""

        if video_type == VideoType.LONG.value:
            team = create_script_analysis_team()
        else:
            team = create_reel_script_analysis_team()

        try:
            result = await team.run(task=task)
            return self._extract_final_message(result)
        except Exception as e:
            logger.error(
                f"Error in generate_script_using_data: {e}", exc_info=True
            )
            return f"Error generating script: {str(e)}"

    async def generate_script_using_topic(self, task, video_type):
        """Generate script using topic-based workflow."""

        if video_type == VideoType.LONG.value:
            team = create_video_team()
        else:
            team = create_reel_team()

        try:
            result = await team.run(task=task)
            logger.debug(f"Script generation result: {result}")
            return self._extract_final_message(result)
        except Exception as e:
            logger.error(
                f"Error in generate_script_using_topic: {e}", exc_info=True
            )
            return f"Error generating script: {str(e)}"

    async def generate_script_from_latest_news(self, task, video_type):
        """Generate script from latest news workflow."""

        if video_type == VideoType.LONG.value:
            team = create_video_team()
        else:
            team = create_reel_team()

        try:
            result = await team.run(task=task)
            return self._extract_final_message(result)
        except Exception as e:
            logger.error(
                f"Error in generate_script_from_latest_news: {e}", exc_info=True
            )
            return f"Error generating script: {str(e)}"

    def _extract_final_message(self, result) -> str:
        """Extract the final message from team run result."""
        try:
            if hasattr(result, "messages") and result.messages:
                # Get the last message from the conversation
                last_message = result.messages[-1]
                if hasattr(last_message, "content"):
                    return last_message.content
                return str(last_message)
            elif hasattr(result, "content"):
                return result.content
            else:
                return str(result)
        except Exception as e:
            logger.error(f"Error extracting final message: {e}", exc_info=True)
            return "Script generation completed but could not extract result."

    # Synchronous wrapper methods for backward compatibility
    def script_using_video_sync(
        self, topic, video_type, keywords, link=None, video_link=None
    ):
        """Synchronous wrapper for script_using_video."""
        return asyncio.run(
            self.script_using_video(topic, video_type, keywords, link, video_link)
        )

    def script_using_blog_sync(self, topic, video_type, keywords, link):
        """Synchronous wrapper for script_using_blog."""
        return asyncio.run(self.script_using_blog(topic, video_type, keywords, link))

    def script_using_script_sync(self, topic, video_type, keywords):
        """Synchronous wrapper for script_using_script."""
        return asyncio.run(self.script_using_script(topic, video_type, keywords))

    def script_using_topic_sync(self, topic, video_type, keywords):
        """Synchronous wrapper for script_using_topic."""
        return asyncio.run(self.script_using_topic(topic, video_type, keywords))

    def script_from_latest_news_sync(self, video_type, keywords):
        """Synchronous wrapper for script_from_latest_news."""
        return asyncio.run(self.script_from_latest_news(video_type, keywords))

    def generate_script_contents_sync(self, script):
        """Synchronous wrapper for generate_script_contents."""
        return asyncio.run(self.generate_script_contents(script))


# Legacy function for backward compatibility
def generate_script_content(task):
    """Legacy function for backward compatibility."""
    workflow = ScriptWorkFlow()
    return workflow.generate_script_contents_sync(task)
