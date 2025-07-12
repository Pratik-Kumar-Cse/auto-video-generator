import logging
from proglog import ProgressBarLogger  # type: ignore
from typing import Any


class ProgressLogger(ProgressBarLogger):
    def __init__(self, task: Any, log_level: int = logging.INFO):
        """
        Initialize the ProgressLogger with a task and log level.

        :param task: The task object for updating progress.
        :param log_level: The logging level (default: logging.INFO).
        """
        super().__init__()
        self.last_message = ""
        self.previous_percentage = 0
        self.task = task

        # Set up logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        # Create console handler and set level
        ch = logging.StreamHandler()
        ch.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Add formatter to ch
        ch.setFormatter(formatter)

        # Add ch to logger
        self.logger.addHandler(ch)

    def callback(self, **changes: Any) -> None:
        """
        Update the last message with the latest changes from the logger.

        :param changes: Keyword arguments containing updated parameters.
        """
        for parameter, value in changes.items():
            self.last_message = value

    def bars_callback(self, bar, attr, value, old_value=None) -> None:
        """
        Handle progress updates and send events for video processing.

        :param bar: The progress bar being updated.
        :param attr: The attribute of the bar being updated.
        :param value: The new value of the attribute.
        :param old_value: The previous value of the attribute (optional).
        """
        if "Writing video" in self.last_message:
            percentage = (value / self.bars[bar]["total"]) * 100
            self.logger.info(f"Progress: {int(percentage)}%")
            if percentage > 0 and percentage < 100:
                new_percentage = int(int(percentage) * 60 / 100) + 40
                if int(new_percentage) != self.previous_percentage:
                    self.previous_percentage = int(new_percentage)
                    self.task.update_state(
                        state="PROGRESS",
                        meta={
                            "progress": new_percentage,
                            "status": "video generating ...",
                        },
                    )
