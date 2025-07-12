import logging
from typing import Sequence

from app.core.config import settings
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.tools.mcp import StreamableHttpServerParams, mcp_server_tools

from ..model_factory import ModelFactory
from .prompts import (
    ANALYSE_AGENT_PROMPT,
    ARTICLE_ANALYSE_AGENT_PROMPT,
    CONTENT_AGENT_PROMPT,
    CONTENT_AGENT_REEL_PROMPT,
    FORMATTER_AGENT_PROMPT,
    INTRO_HOOK_AGENT_PROMPT,
    INTRO_HOOK_REEL_AGENT_PROMPT,
    OUTRO_AGENT_PROMPT,
    SCENE_CREATOR_AGENT_PROMPT,
    SCRIPT_ANALYSE_AGENT_PROMPT,
    SPOKEN_ENGLISH_AGENT_PROMPT,
    TITLE_AGENT_PROMPT,
    TONE_AGENT_PROMPT,
    TONE_AGENT_REEL_PROMPT,
)

# Initialize logger
logger = logging.getLogger(__name__)


# Initialize Exa tools - temporarily disabled due to MCP compatibility issues
exa_params = StreamableHttpServerParams(
    url=f"https://mcp.exa.ai/mcp?exaApiKey={settings.EXA_API_KEY}"
)
exa_tools = mcp_server_tools(exa_params)
# exa_tools = []  # Placeholder until MCP tools are available


def search_tool(query: str) -> str:
    """
    Placeholder search tool function.
    MCP search functionality temporarily disabled.
    """
    return f"Search functionality temporarily disabled. Query was: {query}"


# Create model configuration
model_config = {
    "llm_type": "openai",
    "provider": "OpenAIChatCompletionClient",
    "model": "gpt-4o",
    "api_key": settings.REQUESTY_KEY,
    "base_url": "https://router.requesty.ai/v1",
    "temperature": 0.7,
}


# Create shared model client
model_client = ModelFactory.create_model_client(model_config)


# Code executor for tools
code_executor = LocalCommandLineCodeExecutor(work_dir="coding")

# User proxy agent
user_proxy = UserProxyAgent("Admin")

# Master Agent
logger.info("Creating Master Agent")
Master_Agent = AssistantAgent(
    name="Master_Agent",
    system_message="""
    You are a helpful AI assistant that determines
    from the previous chat whether the user is asking for a reel or a video.
    If the user doesn't mention explicitly consider it a video .
    If the user say that the video is 60 sec or less consider it is a reel.
    If it is a reel say "It is a reel." else say "It is a video.
    """,
    model_client=model_client,
)
logger.info("Master Agent created successfully")

# Research Agent - tools temporarily disabled
Research_Agent = AssistantAgent(
    name="Research_Agent",
    system_message="""
    Your input is the output of the user_proxy agent.
    Research functionality temporarily disabled due to MCP issues.
    """,
    model_client=model_client,
)

# Transcript Agent
Transcript_Agent = AssistantAgent(
    name="Transcript_Agent",
    system_message="""
    Your input is the output of the user_proxy agent.
    Only use the tool you have been provided with.
    """,
    model_client=model_client,
)

# Analysis Agents
Analyse_Agent = AssistantAgent(
    name="Analyse_Agent",
    system_message=ANALYSE_AGENT_PROMPT,
    model_client=model_client,
)

Article_Analyse_Agent = AssistantAgent(
    name="Article_Analyse_Agent",
    system_message=ARTICLE_ANALYSE_AGENT_PROMPT,
    model_client=model_client,
)

Script_Analyse_Agent = AssistantAgent(
    name="Script_Analyse_Agent",
    system_message=SCRIPT_ANALYSE_AGENT_PROMPT,
    model_client=model_client,
)

# Content Generation Agents
Tone_Agent = AssistantAgent(
    name="Tone_Agent",
    system_message=TONE_AGENT_PROMPT,
    model_client=model_client,
)

Title_agent = AssistantAgent(
    name="Title_Agent",
    system_message=TITLE_AGENT_PROMPT,
    model_client=model_client,
)

Intro_Hook_Agent = AssistantAgent(
    name="Intro_Hook_Agent",
    system_message=INTRO_HOOK_AGENT_PROMPT,
    model_client=model_client,
)

Content_Agent = AssistantAgent(
    name="Content_Agent",
    system_message=CONTENT_AGENT_PROMPT,
    model_client=model_client,
)

Outro_Agent = AssistantAgent(
    name="Outro_Agent",
    system_message=OUTRO_AGENT_PROMPT,
    model_client=model_client,
)

Formatter_Agent = AssistantAgent(
    name="Formatter_Agent",
    system_message=FORMATTER_AGENT_PROMPT,
    model_client=model_client,
)

Spoken_English_Agent = AssistantAgent(
    name="Spoken_English_Agent",
    system_message=SPOKEN_ENGLISH_AGENT_PROMPT,
    model_client=model_client,
)

# Reel-specific agents
Intro_Hook_Agent_Reel = AssistantAgent(
    name="Intro_Hook_Agent_Reel",
    system_message=INTRO_HOOK_REEL_AGENT_PROMPT,
    model_client=model_client,
)

Content_Agent_Reel = AssistantAgent(
    name="Content_Agent_Reel",
    system_message=CONTENT_AGENT_REEL_PROMPT,
    model_client=model_client,
)

Tone_Agent_Reel = AssistantAgent(
    name="Tone_Agent_Reel",
    system_message=TONE_AGENT_REEL_PROMPT,
    model_client=model_client,
)

Reviewer_Agent = AssistantAgent(
    name="Reviewer",
    system_message="""
    You are Reviewer. Your task is to check and validate the facts
    in the content by Tone_Agent_Reel.
    If you find the facts are not correct, either correct them or
    remove them. Also adjust sentence structure if you remove them.
    Don't do any other changes.
    only return the script in text.
    """,
    model_client=model_client,
)

Scene_Creator_Agent = AssistantAgent(
    name="Scene_Creator_Agent",
    system_message=SCENE_CREATOR_AGENT_PROMPT,
    model_client=model_client,
)

# Termination conditions
text_termination = TextMentionTermination("TERMINATE")
max_messages_termination = MaxMessageTermination(max_messages=10)
termination_condition = text_termination | max_messages_termination

# Selector functions for different workflows


def video_selector_func(
    messages: Sequence[BaseAgentEvent | BaseChatMessage],
) -> str | None:
    """Selector function for video generation workflow."""
    if not messages:
        logger.info("Starting video generation workflow with Research Agent")
        return Research_Agent.name

    last_message = messages[-1]

    # Define the workflow sequence
    workflow_sequence = [
        Research_Agent.name,
        Title_agent.name,
        Content_Agent.name,
        Tone_Agent.name,
        Intro_Hook_Agent.name,
        Outro_Agent.name,
        Spoken_English_Agent.name,
        Formatter_Agent.name,
    ]

    current_speaker = last_message.source
    logger.debug(f"Current speaker in video workflow: {current_speaker}")

    try:
        current_index = workflow_sequence.index(current_speaker)
        if current_index < len(workflow_sequence) - 1:
            next_agent = workflow_sequence[current_index + 1]
            logger.info(f"Video workflow: {current_speaker} -> {next_agent}")
            return next_agent
        else:
            logger.info("Video workflow completed")
    except ValueError:
        logger.warning(f"Unknown speaker in video workflow: {current_speaker}")

    return None


def analysis_selector_func(
    messages: Sequence[BaseAgentEvent | BaseChatMessage],
) -> str | None:
    """Selector function for analysis-based workflow."""
    if not messages:
        return Analyse_Agent.name

    last_message = messages[-1]

    # Define the workflow sequence
    workflow_sequence = [
        Analyse_Agent.name,
        Title_agent.name,
        Content_Agent.name,
        Tone_Agent.name,
        Intro_Hook_Agent.name,
        Outro_Agent.name,
        Spoken_English_Agent.name,
        Formatter_Agent.name,
    ]

    current_speaker = last_message.source

    try:
        current_index = workflow_sequence.index(current_speaker)
        if current_index < len(workflow_sequence) - 1:
            return workflow_sequence[current_index + 1]
    except ValueError:
        pass

    return None


def reel_selector_func(
    messages: Sequence[BaseAgentEvent | BaseChatMessage],
) -> str | None:
    """Selector function for reel generation workflow."""
    if not messages:
        logger.info("Starting reel generation workflow with Research Agent")
        return Research_Agent.name

    last_message = messages[-1]

    # Define the workflow sequence
    workflow_sequence = [
        Research_Agent.name,
        Intro_Hook_Agent_Reel.name,
        Content_Agent_Reel.name,
        Tone_Agent_Reel.name,
        Reviewer_Agent.name,
    ]

    current_speaker = last_message.source
    logger.debug(f"Current speaker in reel workflow: {current_speaker}")

    try:
        current_index = workflow_sequence.index(current_speaker)
        if current_index < len(workflow_sequence) - 1:
            next_agent = workflow_sequence[current_index + 1]
            logger.info(f"Reel workflow: {current_speaker} -> {next_agent}")
            return next_agent
        else:
            logger.info("Reel workflow completed")
    except ValueError:
        logger.warning(f"Unknown speaker in reel workflow: {current_speaker}")

    return None


# Team creation functions


def create_video_team():
    """Create a team for video script generation."""
    logger.info("Creating video script generation team")

    team = SelectorGroupChat(
        [
            Research_Agent,
            Title_agent,
            Content_Agent,
            Tone_Agent,
            Intro_Hook_Agent,
            Outro_Agent,
            Spoken_English_Agent,
            Formatter_Agent,
        ],
        model_client=model_client,
        termination_condition=termination_condition,
        selector_func=video_selector_func,
    )

    logger.info("Video script generation team created successfully")
    return team


def create_analysis_team():
    """Create a team for analysis-based script generation."""
    return SelectorGroupChat(
        [
            Analyse_Agent,
            Title_agent,
            Content_Agent,
            Tone_Agent,
            Intro_Hook_Agent,
            Outro_Agent,
            Spoken_English_Agent,
            Formatter_Agent,
        ],
        model_client=model_client,
        termination_condition=termination_condition,
        selector_func=analysis_selector_func,
    )


def create_article_analysis_team():
    """Create a team for article analysis-based script generation."""
    return SelectorGroupChat(
        [
            Article_Analyse_Agent,
            Title_agent,
            Content_Agent,
            Tone_Agent,
            Intro_Hook_Agent,
            Outro_Agent,
            Spoken_English_Agent,
            Formatter_Agent,
        ],
        model_client=model_client,
        termination_condition=termination_condition,
        selector_func=analysis_selector_func,
    )


def create_script_analysis_team():
    """Create a team for script analysis-based generation."""
    return SelectorGroupChat(
        [
            Script_Analyse_Agent,
            Title_agent,
            Content_Agent,
            Tone_Agent,
            Intro_Hook_Agent,
            Outro_Agent,
            Spoken_English_Agent,
            Formatter_Agent,
        ],
        model_client=model_client,
        termination_condition=termination_condition,
        selector_func=analysis_selector_func,
    )


def create_reel_team():
    """Create a team for reel script generation."""
    logger.info("Creating reel script generation team")

    team = SelectorGroupChat(
        [
            Research_Agent,
            Intro_Hook_Agent_Reel,
            Content_Agent_Reel,
            Tone_Agent_Reel,
            Reviewer_Agent,
        ],
        model_client=model_client,
        termination_condition=termination_condition,
        selector_func=reel_selector_func,
    )

    logger.info("Reel script generation team created successfully")
    return team


def create_reel_analysis_team():
    """Create a team for reel analysis-based generation."""
    return SelectorGroupChat(
        [
            Analyse_Agent,
            Intro_Hook_Agent_Reel,
            Content_Agent_Reel,
            Tone_Agent_Reel,
            Reviewer_Agent,
        ],
        model_client=model_client,
        termination_condition=termination_condition,
        selector_func=reel_selector_func,
    )


def create_reel_article_analysis_team():
    """Create a team for reel article analysis-based generation."""
    return SelectorGroupChat(
        [
            Article_Analyse_Agent,
            Intro_Hook_Agent_Reel,
            Content_Agent_Reel,
            Tone_Agent_Reel,
            Reviewer_Agent,
        ],
        model_client=model_client,
        termination_condition=termination_condition,
        selector_func=reel_selector_func,
    )


def create_reel_script_analysis_team():
    """Create a team for reel script analysis-based generation."""
    return SelectorGroupChat(
        [
            Script_Analyse_Agent,
            Intro_Hook_Agent_Reel,
            Content_Agent_Reel,
            Tone_Agent_Reel,
            Reviewer_Agent,
        ],
        model_client=model_client,
        termination_condition=termination_condition,
        selector_func=reel_selector_func,
    )


# Legacy compatibility functions (for backward compatibility)


def custom_speaker_selection_func(last_speaker, groupchat):
    """Legacy function for backward compatibility."""
    messages = groupchat.messages if hasattr(groupchat, "messages") else []
    return video_selector_func(messages)


def custom_speaker_selection_func1(last_speaker, groupchat):
    """Legacy function for backward compatibility."""
    messages = groupchat.messages if hasattr(groupchat, "messages") else []
    return analysis_selector_func(messages)


def custom_speaker_selection_func2(last_speaker, groupchat):
    """Legacy function for backward compatibility."""
    messages = groupchat.messages if hasattr(groupchat, "messages") else []
    return analysis_selector_func(messages)


def custom_speaker_selection_func3(last_speaker, groupchat):
    """Legacy function for backward compatibility."""
    messages = groupchat.messages if hasattr(groupchat, "messages") else []
    return analysis_selector_func(messages)


def custom_speaker_selection_func4(last_speaker, groupchat):
    """Legacy function for backward compatibility."""
    messages = groupchat.messages if hasattr(groupchat, "messages") else []
    return video_selector_func(messages)


def custom_speaker_selection_func_reel(last_speaker, groupchat):
    """Legacy function for backward compatibility."""
    messages = groupchat.messages if hasattr(groupchat, "messages") else []
    return reel_selector_func(messages)


def custom_speaker_selection_func_reel1(last_speaker, groupchat):
    """Legacy function for backward compatibility."""
    messages = groupchat.messages if hasattr(groupchat, "messages") else []
    return reel_selector_func(messages)


def custom_speaker_selection_func_reel2(last_speaker, groupchat):
    """Legacy function for backward compatibility."""
    messages = groupchat.messages if hasattr(groupchat, "messages") else []
    return reel_selector_func(messages)


def custom_speaker_selection_func_reel3(last_speaker, groupchat):
    """Legacy function for backward compatibility."""
    messages = groupchat.messages if hasattr(groupchat, "messages") else []
    return reel_selector_func(messages)


def custom_speaker_selection_func_reel4(last_speaker, groupchat):
    """Legacy function for backward compatibility."""
    messages = groupchat.messages if hasattr(groupchat, "messages") else []
    return reel_selector_func(messages)
