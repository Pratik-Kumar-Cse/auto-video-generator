from autogen.agentchat import (
    Agent,
    AssistantAgent,
    GroupChat,
    GroupChatManager,
    UserProxyAgent,
)
from model_config import AIConfigManager
from autogen.cache import Cache


config_list = AIConfigManager().get_provider_configs()

llm_config = {
    "config_list": config_list,
    "timeout": 180,
    "cache_seed": None,
}


assistant_1 = AssistantAgent(
    name="Assistant_1",
    llm_config={"config_list": config_list},
)

Scene_creator_Agent = AssistantAgent(
    name="Scene_creator_Agent",
    system_message="""
    You are the Scene_creator Agent responsible for processing the video script and dividing it into distinct scenes for a video script.

    Your tasks are to:
    1. Carefully review the provided video script.
    2. Divide the script into multiple logical scenes based on:
       - Content shifts
       - Theme changes
       - Narrative progression
       - Setting changes
       - Time jumps or transitions
    3. Present each scene's content exactly as it appears in the original script, without any additional descriptions or modifications.

    Format your response as a list of strings, where each string represents a scene's content don't add ```python:

    {
     scenes: ["Scene 1 content goes here...",
     "Scene 2 content goes here...",
     "Scene 3 content goes here...",
     ...]
     }

    Guidelines:
    - Do not add any descriptions, summaries, or extra information to the scenes.
    - Preserve the original script's exact wording, formatting, and style.
    - Ensure that the division into scenes is logical and maintains the flow of the narrative.
    - Do not number or label the scenes within the content strings.
    """,
    llm_config={"config_list": config_list, "cache_seed": None},
)

Hook_Generator_Agent = AssistantAgent(
    name="Hook_Generator_Agent",
    system_message="""
    You are the Hook_Generator_Agent, tasked with creating compelling hooks for each scene in a video script. Your goal is to capture the audience's attention and draw them into the content.

    Your responsibilities include:
    1. Analyzing the content of each scene provided by the Scene_creator_Agent.
    2. Generating a captivating hook for each scene that:
    - Teases the main topic or conflict of the scene
    - Creates curiosity or intrigue
    - Relates to the target audience's interests
    - Is concise and impactful (typically 1-2 sentences)

    Format your response as a list of strings, where each string is a hook corresponding to a scene:

    {
    hooks: ["Hook for Scene 1 goes here...",
    "Hook for Scene 2 goes here...",
    "Hook for Scene 3 goes here...",
    ...]
    }

    Guidelines:
    - Ensure each hook is unique and tailored to its specific scene.
    - Use engaging language, questions, or statements that provoke thought.
    - Avoid revealing too much information; the goal is to entice, not summarize.
    - Consider the overall tone and style of the video when crafting hooks.
    """,
    llm_config={"config_list": config_list, "cache_seed": None},
)

Flow_Enhancer_Agent = AssistantAgent(
    name="Flow_Enhancer_Agent",
    system_message="""
    You are the Flow_Enhancer_Agent, responsible for improving the narrative flow between scenes in a video script. Your task is to ensure smooth transitions and maintain audience engagement throughout the video.

    Your duties include:
    1. Reviewing the scenes provided by the Scene_creator_Agent.
    2. Identifying potential gaps or abrupt shifts between scenes.
    3. Suggesting transition elements or narrative bridges to connect scenes seamlessly.

    Format your response as a list of strings, where each string is a flow enhancement suggestion between two scenes:

    {
    flow_enhancements: ["Suggestion between Scene 1 and 2 goes here...",
    "Suggestion between Scene 2 and 3 goes here...",
    "Suggestion between Scene 3 and 4 goes here...",
    ...]
    }

    Guidelines:
    - Focus on creating logical and smooth transitions between scenes.
    - Suggest brief narrative elements, visual transitions, or thematic links.
    - Ensure that your suggestions maintain the overall tone and style of the video.
    - Be concise; each suggestion should be 1-3 sentences long.
    """,
    llm_config={"config_list": config_list, "cache_seed": None},
)

Engagement_Booster_Agent = AssistantAgent(
    name="Engagement_Booster_Agent",
    system_message="""
    You are the Engagement_Booster_Agent, tasked with enhancing viewer engagement for each scene in a video script. Your goal is to suggest elements that will keep the audience interested and invested in the content.

    Your responsibilities include:
    1. Analyzing each scene provided by the Scene_creator_Agent.
    2. Proposing engagement-boosting elements such as:
    - Rhetorical questions
    - Interesting facts or statistics
    - Relatable examples or analogies
    - Call-to-action prompts
    - Interactive elements (if applicable to the video format)

    Format your response as a list of strings, where each string contains engagement suggestions for a scene:

    {
    engagement_boosters: ["Engagement suggestions for Scene 1 go here...",
    "Engagement suggestions for Scene 2 go here...",
    "Engagement suggestions for Scene 3 go here...",
    ...]
    }

    Guidelines:
    - Tailor suggestions to the content and tone of each specific scene.
    - Ensure that engagement elements add value without disrupting the main message.
    - Be creative but relevant; all suggestions should enhance the viewer's experience.
    - Keep suggestions concise, typically 2-3 ideas per scene.
    """,
    llm_config={"config_list": config_list, "cache_seed": None},
)

Trend_Incorporator_Agent = AssistantAgent(
    name="Trend_Incorporator_Agent",
    system_message="""
    You are the Trend_Incorporator_Agent, responsible for suggesting current trends, popular references, or timely elements that can be incorporated into each scene of the video script to increase its relevance and appeal.

    Your tasks include:
    1. Reviewing each scene provided by the Scene_creator_Agent.
    2. Identifying opportunities to incorporate:
    - Current social media trends
    - Popular culture references
    - Recent news or events (if appropriate)
    - Trending hashtags or phrases
    - Up-to-date statistics or data

    Format your response as a list of strings, where each string contains trend incorporation suggestions for a scene:

    {
    trend_suggestions: ["Trend ideas for Scene 1 go here...",
    "Trend ideas for Scene 2 go here...",
    "Trend ideas for Scene 3 go here...",
    ...]
    }

    Guidelines:
    - Ensure all trend suggestions are relevant to the scene's content and overall video theme.
    - Prioritize trends that will resonate with the target audience.
    - Be mindful of the video's longevity; avoid extremely short-lived trends if possible.
    - Provide brief explanations of how each trend can be incorporated (1-2 sentences per suggestion).
    - Remember that trends should enhance, not overshadow, the main content of the scene.
    """,
    llm_config={"config_list": config_list, "cache_seed": None},
)

writer = AssistantAgent(
    name="Writer",
    llm_config={"config_list": config_list},
    system_message="""
    You are a professional writer write the scene, hook, flow, engagement and trend for each scene in a json.
    
    return format example
    
    {
        "scenes": [
            {
                "scene": "scene 1",
                "hook": "hook 1",
                "flow": "flow 1",
                "engagement": "engagement 1",
                "trend": "trend 1"
            },
            {
                "scene": "scene 2",
                "hook": "hook 2",
                "flow": "flow 2",
                "engagement": "engagement 2",
                "trend": "trend 2"
            },
            ....
        ]
    }
    """,
)

user = UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    code_execution_config={
        "last_n_messages": 1,
        "work_dir": "tasks",
        "use_docker": False,
    },
)


def writing_message(recipient, messages, sender, config):
    return f"Polish the content to make an engaging and nicely formatted blog post. \n\n {recipient.chat_messages_for_summary(sender)[-1]['content']}"


nested_chat_queue = [
    {
        "recipient": Scene_creator_Agent,
        "message": "Create the multiple scene of the script",
        "summary_method": "last_msg",
        "max_turns": 1,
    },
    {
        "recipient": Hook_Generator_Agent,
        "message": "create hook for each video scene",
        "summary_method": "last_msg",
        "max_turns": 1,
    },
    {
        "recipient": Flow_Enhancer_Agent,
        "message": "create flow for each video scene",
        "summary_method": "last_msg",
        "max_turns": 1,
    },
    {
        "recipient": Engagement_Booster_Agent,
        "message": "generate the engagement of each video scene.",
        "summary_method": "last_msg",
        "max_turns": 1,
    },
    {
        "recipient": Trend_Incorporator_Agent,
        "message": "generate the trend of each video scene.",
        "summary_method": "last_msg",
        "max_turns": 1,
    },
    {
        "recipient": writer,
        "message": writing_message,
        "summary_method": "last_msg",
        "max_turns": 1,
    },
]


def custom_speaker_selection_func(last_speaker: Agent, groupchat: GroupChat):
    if last_speaker is user:
        return Scene_creator_Agent
    elif last_speaker is Scene_creator_Agent:
        return Hook_Generator_Agent
    elif last_speaker is Hook_Generator_Agent:
        return Flow_Enhancer_Agent
    elif last_speaker is Flow_Enhancer_Agent:
        return Engagement_Booster_Agent
    elif last_speaker is Engagement_Booster_Agent:
        return Trend_Incorporator_Agent
    elif last_speaker is Trend_Incorporator_Agent:
        return writer
    elif last_speaker is writer:
        pass
    else:
        return "auto"


def generate_script_content(task):

    groupchat = GroupChat(
        agents=[
            Scene_creator_Agent,
            Flow_Enhancer_Agent,
            Hook_Generator_Agent,
            Trend_Incorporator_Agent,
            Engagement_Booster_Agent,
            writer,
        ],
        messages=[],
        max_round=12,
        speaker_selection_method=custom_speaker_selection_func,
    )

    manager = GroupChatManager(
        groupchat=groupchat, llm_config={"config_list": config_list, "cache_seed": None}
    )

    with Cache.disk(cache_seed=44) as cache:
        chat_history = user.initiate_chat(
            manager,
            message=task,
            cache=cache,
            max_turns=1,
            summary_method="reflection_with_llm",
            summary_args={
                "summary_prompt": "Return the last agent response exact in json format dont add this tag ```json"
            },
        )

    groupchat.reset()
    manager.reset()
    user.reset()

    return chat_history.summary
