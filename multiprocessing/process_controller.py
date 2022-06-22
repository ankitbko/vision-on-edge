"""This module is used to provide the process controller."""

import logging
from multiprocessing import Process
from multiprocessing.context import DefaultContext
from process_queue import ProcessQueue

import frame_provider
from frame_processor import FrameProcessor

class ProcessController:
    """
    Process controller for start stop restarting the processes.
    """

    def __init__(self, multiprocessing_context: DefaultContext) -> None:
        """
        Initialize the process controller.
        @param:
            multiprocessing_context (DefaultContext): Multiprocessing context
        """
        self.multiprocessing_context = multiprocessing_context
        self.queue = ProcessQueue()
        self.process_one = None
        self.process_two = None
        self.logger = logging.getLogger(__name__)

    def start(self) -> bool:
        """
        Start the processes.
        @return:
            success (bool): True if the processes are started successfully, False otherwise
        """
        self.logger.info("Starting all processes...")
        if self.process_one is not None and self.process_one.is_alive():
            self.logger.info("process_one is already running...")
            return False
        if self.process_two is not None and self.process_two.is_alive():
            self.logger.info("process_two is already running...")
            return False

        # Creating empty queue
        self.queue = ProcessQueue()
        # Creating process one
        self.process_one = self.multiprocessing_context.Process(
            target=frame_provider.run,
            args=((self.queue),),
            name="ProcessOne",
        )
        # Starting process one as a daemon process
        self.process_one.daemon = True
        self.process_one.start()

        # Creating process two
        self.process_two = self.multiprocessing_context.Process(
            target=FrameProcessor().run,
            args=((self.queue),),
            name="ProcessTwo",
        )
        # Starting process two as a daemon process
        self.process_two.daemon = True
        self.process_two.start()
        self.logger.info("Started all processes...")
        return True

    def stop(self) -> bool:
        """
        Stop the processes.
        @return:
            success (bool): True if the processes are stopped successfully, False otherwise
        """
        self.logger.info("Stopping all processes...")
        if self.process_one is not None and self.process_one.is_alive():
            self._terminate_process(self.process_one)
            self.process_one = None
            self.logger.info("process_one is stopped...")
        if self.process_two is not None and self.process_two.is_alive():
            self._terminate_process(self.process_two)
            self.process_two = None
            self.logger.info("process_two is stopped...")

        # Empty queue
        self.queue.work_queue.close()
        self.logger.info("Queue is cleared...")
        self.logger.info("Stopped all processes...")
        return True

    def restart(self) -> bool:
        """
        Restart the processes.
        @return:
            success (bool): True if the processes are restarted successfully, False otherwise
        """
        self.logger.info("Restarting all processes...")
        self.stop()
        result = self.start()
        self.logger.info("Restarted all processes...")
        return result

    def _terminate_process(self, process: Process, retry_count: int = 0) -> None:
        """
        Terminate the process with retry (internal).
        @param:
            process (Process): Process object
            retry_count (int): Retry count
        """
        self.logger.info(f"Terminating process {process.name}...")
        if retry_count < 3:
            try:
                process.terminate()
            except Exception as e:
                self.logger.exception(e)
                self.logger.error(e)
                self._terminate_process(process, retry_count + 1)
        else:
            self.logger.error(f"Could not terminate process {process.name}...")
            raise Exception(f"Could not terminate process {process.name}...")
