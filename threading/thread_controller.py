"""This module is used to provide the thread controller."""

import logging
import threading
from thread_queue import ThreadQueue

import frame_provider
from frame_processor import FrameProcessor


class ThreadController:
    """
    Thread controller for start stop restarting the threads.
    """

    def __init__(self) -> None:
        """
        Initialize the thread controller.
        """
        self.queue = ThreadQueue()
        self.thread_one = None
        self.thread_two = None
        self.logger = logging.getLogger(__name__)

    def start(self) -> bool:
        """
        Start the threads.
        @return:
            success (bool): True if the threads are started successfully, False otherwise
        """
        self.logger.info("Starting all threads...")
        if self.thread_one is not None and self.thread_one.is_alive():
            self.logger.info("thread_one is already running...")
            return False
        if self.thread_two is not None and self.thread_two.is_alive():
            self.logger.info("thread_two is already running...")
            return False

        # Creating empty queue
        self.queue = ThreadQueue()

        # Creating thread one
        self.thread_one = threading.Thread(
            target=frame_provider.run, args=((self.queue),), name="ThreadOne",
        )
        # Starting thread one as a daemon thread
        self.thread_one.setDaemon(True)
        self.thread_one.start()

        # Creating thread two
        self.thread_two = threading.Thread(
            target=FrameProcessor().run, args=((self.queue),), name="ThreadTwo",
        )
        # Starting thread two as a daemon thread
        self.thread_two.setDaemon(True)
        self.thread_two.start()
        self.logger.info("Started all threads...")
        return True

    def stop(self) -> bool:
        """
        Stop the threads.
        @return:
            success (bool): True if the threads are stopped successfully, False otherwise
        """
        self.logger.info("Stopping all threads...")
        if self.thread_one is not None and self.thread_one.is_alive():
            self._terminate_thread(self.thread_one)
            self.thread_one = None
            self.logger.info("thread_one is stopped...")
        if self.thread_two is not None and self.thread_two.is_alive():
            self._terminate_thread(self.thread_two)
            self.thread_two = None
            self.logger.info("thread_two is stopped...")

        # Empty queue
        # self.queue.work_queue.close()
        # self.logger.info("Queue is cleared...")
        self.logger.info("Stopped all threads...")
        return True

    def restart(self) -> bool:
        """
        Restart the threads.
        @return:
            success (bool): True if the threads are restarted successfully, False otherwise
        """
        self.logger.info("Restarting all threads...")
        self.stop()
        result = self.start()
        self.logger.info("Restarted all threads...")
        return result

    def _terminate_thread(self, thread: threading.Thread, retry_count: int = 0) -> None:
        """
        Terminate the thread with retry (internal).
        @param:
            thread (thread): thread object
            retry_count (int): Retry count
        """
        self.logger.info(f"Terminating thread {thread.name}...")
        if retry_count < 3:
            try:
                thread.join(timeout=1)
            except Exception as e:
                self.logger.exception(e)
                self.logger.error(e)
                self._terminate_thread(thread, retry_count + 1)
        else:
            self.logger.error(f"Could not terminate thread {thread.name}...")
            raise Exception(f"Could not terminate thread {thread.name}...")
