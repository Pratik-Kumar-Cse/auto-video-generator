# type: ignore
from app.helper.sse_manager import SseManager
from app.constant.constant import SSE_EVENT_NAME
from app.constant.enum.event_enum import EventStream, EventProcessType
from app.loggers.logger import get_logger


class ScriptLogger:
    def __init__(self, video_id, client_id, number_of_tern):
        """
        Initialize the ScriptLogger with a video ID.

        :param video_id: Unique identifier for the video being processed.
        :param client_id: Client identifier for SSE communication.
        :param number_of_tern: Total number of turns/steps in the process.
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.sse_manager = SseManager()
        self.previous_percentage = None
        self.video_id = video_id
        self.client_id = client_id
        self.number_of_tern = number_of_tern
        
        self.logger.info(
            f"ScriptLogger initialized for video_id={video_id}, "
            f"client_id={client_id}, turns={number_of_tern}"
        )

    def update_status(self, index, message, data):
        """
        Handle progress updates and send events for script processing.

        :param index: Current step index in the process.
        :param message: Status message to display.
        :param data: Additional data to include in the update.
        """
        index = index + 1
        percentage = (index / self.number_of_tern) * 100
        
        self.logger.debug(
            f"Script progress update: step {index}/{self.number_of_tern} "
            f"({percentage:.1f}%) - {message}"
        )
        
        if int(percentage) != self.previous_percentage:
            self.previous_percentage = int(percentage)
            if self.previous_percentage <= 100:
                try:
                    self.sse_manager.send_update(
                        event_name=SSE_EVENT_NAME.SCRIPT_STREAM,
                        data={
                            "module": EventStream.SCRIPT.value,
                            "message": message,
                            "process_type": (
                                EventProcessType.SCRIPT_GENERATION.value
                            ),
                            "data": {
                                "task_id": self.video_id,
                                "percentage": self.previous_percentage,
                                "agent": data,
                            },
                        },
                        client_id=self.client_id,
                    )
                    
                    self.logger.info(
                        f"SSE update sent: {self.previous_percentage}% - "
                        f"{message}"
                    )
                    
                except Exception as e:
                    self.logger.error(
                        f"Failed to send SSE update: {e}", exc_info=True
                    )
