from autogen.cache import Cache
from app.providers.tavily import search_tool
from functools import partial
import types
from app.agent.script.agents import (
    Master_Agent,
    Analyse_Agent,
    Tone_Agent,
    user_proxy,
    Title_agent,
    Research_Agent,
    Intro_Hook_Agent,
    Tone_Agent_Reel,
    Content_Agent,
    Formatter_Agent,
    Intro_Hook_Agent_Reel,
    Outro_Agent,
    Content_Agent_Reel,
    Spoken_English_Agent,
    Executor_Agent1,
    Reviewer_Agent,
    Article_Analyse_Agent,
    Script_Analyse_Agent,
    Executor_Agent,
    custom_speaker_selection_func,
    custom_speaker_selection_func1,
    custom_speaker_selection_func2,
    custom_speaker_selection_func3,
    custom_speaker_selection_func4,
    custom_speaker_selection_func_reel,
    custom_speaker_selection_func_reel1,
    custom_speaker_selection_func_reel2,
    custom_speaker_selection_func_reel3,
    custom_speaker_selection_func_reel4,
)

from ..stream_data import streamed_print_received_message

from autogen.agentchat import (
    GroupChat,
    GroupChatManager,
)


from app.constant.enum.video_enum import VideoType

from .script import generate_script_content

# from app.service.wisper import process_file
from app.service.utils import save_video

from app.service.web_scrap import extract_article
from app.service.utils import extract_pdf_content_from_url

from ...service.youtube import (
    get_transcription_from_yt_video,
)

from model_config import AIConfigManager

from app.loggers.script_logger import ScriptLogger

config_list = AIConfigManager().get_provider_configs()


class ScriptWorkFlow:

    def __init__(self, logger=None):
        self.logger: ScriptLogger | None = logger

    def script_using_video(
        self, topic, video_type, keywords, link=None, video_link=None
    ):

        if video_link:
            path = save_video(video_link)
            # video_transcript = process_file(path)
        else:
            video_title, video_transcript = get_transcription_from_yt_video(link)
            if not video_transcript:
                video_transcript = search_tool(video_title or topic)

        with Cache.disk(cache_seed=44) as cache:
            user_proxy.initiate_chat(
                Master_Agent, message=topic, cache=cache, max_turns=1
            )

        task = f"""
            topic is: {topic} and video_transcript is: {video_transcript}
            keywords is : {keywords} use these keyword as reference to generate script
            where
                Time: This likely refers to the duration or length of the script.
                Objective: This describes the main goal or purpose of the script.
                Audience: This specifies who the script is intended for.
                Gender: This might refer to the gender of the target audience or the gender of the characters/speakers in the script. 
                Tone: This describes the overall mood or attitude of the script. 
                Speakers: This likely refers to the characters in the script.
            """

        return self.generate_script_using_video(task, video_type)

    def script_using_blog(self, topic, video_type, keywords, link):

        with Cache.disk(cache_seed=44) as cache:
            user_proxy.initiate_chat(
                Master_Agent, message=topic, cache=cache, max_turns=1
            )

        if link.endswith(".pdf"):
            content = extract_pdf_content_from_url(link)
        else:
            content = extract_article(link)

        task = f"""topic is: {topic} and article content : {content}.
        keywords is : {keywords} use these keyword as reference to generate script
        where
            Time: This likely refers to the duration or length of the script.
            Objective: This describes the main goal or purpose of the script.
            Audience: This specifies who the script is intended for.
            Gender: This might refer to the gender of the target audience or the gender of the characters/speakers in the script. 
            Tone: This describes the overall mood or attitude of the script. 
            Speakers: This likely refers to the characters in the script.
        """

        return self.generate_script_using_article(task, video_type)

    def script_using_script(self, topic, video_type, keywords):

        with Cache.disk(cache_seed=44) as cache:
            user_proxy.initiate_chat(
                Master_Agent, message=topic, cache=cache, max_turns=1
            )

        task = f"""this is the topic or script data with instructions: {topic}.
        keywords is : {keywords} use these keyword as reference to generate script
        where
            Time: This likely refers to the duration or length of the script.
            Objective: This describes the main goal or purpose of the script.
            Audience: This specifies who the script is intended for.
            Gender: This might refer to the gender of the target audience or the gender of the characters/speakers in the script. 
            Tone: This describes the overall mood or attitude of the script. 
            Speakers: This likely refers to the characters in the script.
            """
        return self.generate_script_using_data(task, video_type)

    def script_using_topic(self, topic, video_type, keywords):

        with Cache.disk(cache_seed=44) as cache:
            user_proxy.initiate_chat(
                Master_Agent, message=topic, cache=cache, max_turns=1
            )

        task = f"""topic is: {topic}.
        keywords is : {keywords} use these keyword as reference to generate script
        where
            Time: This likely refers to the duration or length of the script.
            Objective: This describes the main goal or purpose of the script.
            Audience: This specifies who the script is intended for.
            Gender: This might refer to the gender of the target audience or the gender of the characters/speakers in the script. 
            Tone: This describes the overall mood or attitude of the script. 
            Speakers: This likely refers to the characters in the script.
        """
        return self.generate_script_using_topic(task, video_type)

    def script_from_latest_news(self, video_type, keywords):

        with Cache.disk(cache_seed=44) as cache:
            user_proxy.initiate_chat(Master_Agent, message="", cache=cache, max_turns=1)

        task = f"""
        Topic: Last week, latest trends groundbreaking news and technologies emerged in the AI, Blockchain. 
        keywords : {keywords} as reference to generate script
        where
            Time: This likely refers to the duration or length of the script.
            Objective: This describes the main goal or purpose of the script.
            Audience: This specifies who the script is intended for.
            Gender: This might refer to the gender of the target audience or the gender of the characters/speakers in the script. 
            Tone: This describes the overall mood or attitude of the script. 
            Speakers: This likely refers to the characters in the script.
            """
        return self.generate_script_from_latest_news(task, video_type)

    def generate_script_contents(self, script):

        task = f"""
            create script scene with hook, flow, engagement and trend for this script.
            script is: {script}
        """

        return generate_script_content(task)

    def generate_script_using_video(self, task, video_type):

        if video_type == VideoType.LONG.value:
            groupchat = GroupChat(
                agents=[
                    user_proxy,
                    Analyse_Agent,
                    Tone_Agent,
                    Title_agent,
                    Intro_Hook_Agent,
                    Content_Agent,
                    Formatter_Agent,
                    Outro_Agent,
                    Spoken_English_Agent,
                ],
                messages=[],
                max_round=12,
                speaker_selection_method=custom_speaker_selection_func1,
            )

        else:

            groupchat = GroupChat(
                agents=[
                    user_proxy,
                    Analyse_Agent,
                    Tone_Agent_Reel,
                    Intro_Hook_Agent_Reel,
                    Content_Agent_Reel,
                    Reviewer_Agent,
                ],
                messages=[],
                max_round=10,
                speaker_selection_method=custom_speaker_selection_func_reel1,
            )

        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": config_list, "cache_seed": None},
        )

        if self.logger:

            index_counter = {"index": 0}
            logger = self.logger

            def streamed_print_received_message_with_queue_and_index(
                self, *args, **kwargs
            ):
                streamed_print_received_message_with_queue = partial(
                    streamed_print_received_message,
                    logger=logger,
                    index=index_counter["index"],
                )
                bound_method = types.MethodType(
                    streamed_print_received_message_with_queue, self
                )
                result = bound_method(*args, **kwargs)
                index_counter["index"] += 1
                return result

            manager._print_received_message = types.MethodType(
                streamed_print_received_message_with_queue_and_index,
                manager,
            )

        with Cache.disk(cache_seed=43) as cache:
            chat_history = user_proxy.initiate_chat(
                manager,
                message=task,
                cache=cache,
                max_turns=1,
                summary_method="reflection_with_llm",
                summary_args={
                    "summary_prompt": "Return the last agent response message in text format"
                },
            )

        groupchat.reset()
        manager.reset()
        user_proxy.reset()

        print("agent cost ====>>>", chat_history.cost)
        return chat_history.summary

    def generate_script_using_article(self, task, video_type):

        if video_type == VideoType.LONG.value:
            groupchat = GroupChat(
                agents=[
                    user_proxy,
                    Article_Analyse_Agent,
                    Tone_Agent,
                    Title_agent,
                    Intro_Hook_Agent,
                    Content_Agent,
                    Formatter_Agent,
                    Outro_Agent,
                    Spoken_English_Agent,
                ],
                messages=[],
                max_round=12,
                speaker_selection_method=custom_speaker_selection_func2,
            )

        else:

            groupchat = GroupChat(
                agents=[
                    user_proxy,
                    Article_Analyse_Agent,
                    Tone_Agent_Reel,
                    Intro_Hook_Agent_Reel,
                    Content_Agent_Reel,
                    Reviewer_Agent,
                ],
                messages=[],
                max_round=10,
                speaker_selection_method=custom_speaker_selection_func_reel2,
            )

        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": config_list, "cache_seed": None},
        )

        if self.logger:

            index_counter = {"index": 0}
            logger = self.logger

            def streamed_print_received_message_with_queue_and_index(
                self, *args, **kwargs
            ):
                streamed_print_received_message_with_queue = partial(
                    streamed_print_received_message,
                    logger=logger,
                    index=index_counter["index"],
                )
                bound_method = types.MethodType(
                    streamed_print_received_message_with_queue, self
                )
                result = bound_method(*args, **kwargs)
                index_counter["index"] += 1
                return result

            manager._print_received_message = types.MethodType(
                streamed_print_received_message_with_queue_and_index,
                manager,
            )

        with Cache.disk(cache_seed=43) as cache:
            chat_history = user_proxy.initiate_chat(
                manager,
                message=task,
                cache=cache,
                max_turns=1,
                summary_method="reflection_with_llm",
                summary_args={
                    "summary_prompt": "Return the last agent response message in text format"
                },
            )

        groupchat.reset()
        manager.reset()
        user_proxy.reset()

        print("agent cost ====>>>", chat_history.cost)
        return chat_history.summary

    def generate_script_using_data(self, task, video_type):

        if video_type == VideoType.LONG.value:
            groupchat = GroupChat(
                agents=[
                    user_proxy,
                    Script_Analyse_Agent,
                    Tone_Agent,
                    Title_agent,
                    Intro_Hook_Agent,
                    Content_Agent,
                    Formatter_Agent,
                    Outro_Agent,
                    Spoken_English_Agent,
                ],
                messages=[],
                max_round=12,
                speaker_selection_method=custom_speaker_selection_func3,
            )

        else:

            groupchat = GroupChat(
                agents=[
                    user_proxy,
                    Script_Analyse_Agent,
                    Tone_Agent_Reel,
                    Intro_Hook_Agent_Reel,
                    Content_Agent_Reel,
                    Reviewer_Agent,
                ],
                messages=[],
                max_round=10,
                speaker_selection_method=custom_speaker_selection_func_reel3,
            )

        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config={
                "config_list": config_list,
                "cache_seed": None,
            },
        )

        if self.logger:

            index_counter = {"index": 0}
            logger = self.logger

            def streamed_print_received_message_with_queue_and_index(
                self, *args, **kwargs
            ):
                streamed_print_received_message_with_queue = partial(
                    streamed_print_received_message,
                    logger=logger,
                    index=index_counter["index"],
                )
                bound_method = types.MethodType(
                    streamed_print_received_message_with_queue, self
                )
                result = bound_method(*args, **kwargs)
                index_counter["index"] += 1
                return result

            manager._print_received_message = types.MethodType(
                streamed_print_received_message_with_queue_and_index,
                manager,
            )

        with Cache.disk(cache_seed=43) as cache:
            chat_history = user_proxy.initiate_chat(
                manager,
                message=task,
                cache=cache,
                max_turns=1,
                summary_method="reflection_with_llm",
                summary_args={
                    "summary_prompt": "Return the last agent response message in text format"
                },
            )
        groupchat.reset()
        manager.reset()
        user_proxy.reset()

        print("agent cost ====>>>", chat_history.cost)
        return chat_history.summary

    def generate_script_using_topic(self, task, video_type):

        if video_type == VideoType.LONG.value:
            groupchat = GroupChat(
                agents=[
                    user_proxy,
                    Research_Agent,
                    Tone_Agent,
                    Title_agent,
                    Intro_Hook_Agent,
                    Content_Agent,
                    Formatter_Agent,
                    Outro_Agent,
                    Spoken_English_Agent,
                    Executor_Agent,
                ],
                messages=[],
                max_round=12,
                speaker_selection_method=custom_speaker_selection_func,
            )

        else:

            groupchat = GroupChat(
                agents=[
                    user_proxy,
                    Research_Agent,
                    Tone_Agent_Reel,
                    Intro_Hook_Agent_Reel,
                    Content_Agent_Reel,
                    Executor_Agent,
                    Reviewer_Agent,
                ],
                messages=[],
                max_round=10,
                speaker_selection_method=custom_speaker_selection_func_reel,
            )

        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": config_list, "cache_seed": None},
        )

        if self.logger:

            index_counter = {"index": 0}
            logger = self.logger

            def streamed_print_received_message_with_queue_and_index(
                self, *args, **kwargs
            ):
                streamed_print_received_message_with_queue = partial(
                    streamed_print_received_message,
                    logger=logger,
                    index=index_counter["index"],
                )
                bound_method = types.MethodType(
                    streamed_print_received_message_with_queue, self
                )
                result = bound_method(*args, **kwargs)
                index_counter["index"] += 1
                return result

            manager._print_received_message = types.MethodType(
                streamed_print_received_message_with_queue_and_index,
                manager,
            )

        with Cache.disk(cache_seed=44) as cache:
            chat_history = user_proxy.initiate_chat(
                manager,
                message=task,
                cache=cache,
                max_turns=1,
                summary_method="reflection_with_llm",
                summary_args={
                    "summary_prompt": "Return the last agent response message in text format"
                },
            )

        groupchat.reset()
        manager.reset()
        user_proxy.reset()

        print("agent cost ====>>>", chat_history.cost)

        return chat_history.summary

    def generate_script_from_latest_news(self, task, video_type):

        if video_type == VideoType.LONG.value:
            groupchat = GroupChat(
                agents=[
                    user_proxy,
                    Research_Agent,
                    Tone_Agent,
                    Title_agent,
                    Intro_Hook_Agent,
                    Content_Agent,
                    Formatter_Agent,
                    Outro_Agent,
                    Spoken_English_Agent,
                    Executor_Agent1,
                    # Scene_Creator_Agent,
                ],
                messages=[],
                max_round=12,
                speaker_selection_method=custom_speaker_selection_func4,
            )

        else:

            groupchat = GroupChat(
                agents=[
                    user_proxy,
                    Research_Agent,
                    Tone_Agent_Reel,
                    Intro_Hook_Agent_Reel,
                    Content_Agent_Reel,
                    Executor_Agent1,
                    Reviewer_Agent,
                    # Scene_Creator_Agent,
                ],
                messages=[],
                max_round=10,
                speaker_selection_method=custom_speaker_selection_func_reel4,
            )

        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": config_list, "cache_seed": None},
        )

        if self.logger:

            index_counter = {"index": 0}
            logger = self.logger

            def streamed_print_received_message_with_queue_and_index(
                self, *args, **kwargs
            ):
                streamed_print_received_message_with_queue = partial(
                    streamed_print_received_message,
                    queue=logger,
                    index=index_counter["index"],
                )
                bound_method = types.MethodType(
                    streamed_print_received_message_with_queue, self
                )
                result = bound_method(*args, **kwargs)
                index_counter["index"] += 1
                return result

            manager._print_received_message = types.MethodType(
                streamed_print_received_message_with_queue_and_index,
                manager,
            )

        with Cache.disk(cache_seed=44) as cache:
            chat_history = user_proxy.initiate_chat(
                manager,
                message=task,
                cache=cache,
                max_turns=1,
                summary_method="reflection_with_llm",
                summary_args={
                    "summary_prompt": "Return the last agent response message in text format"
                },
            )

        groupchat.reset()
        manager.reset()
        user_proxy.reset()

        print("agent cost ====>>>", chat_history.cost)

        return chat_history.summary
