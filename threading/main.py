"""This is the main process."""
import multiprocessing
import sys
import pathlib

sys.path.append(f"{pathlib.Path(__file__).absolute().parent.parent.resolve()}/common")

import logging
import signal
import time
from thread_controller import ThreadController
from multiprocessing.context import DefaultContext
import server

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Process=%(processName)s] [Thread=%(threadName)s] [%(levelname)s]  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def main() -> None:
    """
    Main process.
    """
    logger = logging.getLogger(name="MainProcess")
    logger.info("In main process...")
    logger.info("Calling thread controller start...")
    process_controller = ThreadController()
    try:
        start_server_process(multiprocessing.get_context())
        process_controller.start()
    except Exception as exp:
        logger.exception(exp)
        logger.error(f"Exception while starting thread controller: {exp}")
        sys.exit(1)
    logger.info("Starting the main process...")
    logger.info("Press CTRL+C to stop the process...")
    while True:
        time.sleep(100000000)


def exit_gracefully(*args):
    """
    Exit gracefully, will be called when CTRL+C is pressed.
    """
    logger = logging.getLogger(name="MainProcess")
    logger.warning("Received SIGINT/SIGTERM signal, exiting gracefully...")
    sys.exit(1)


def start_server_process(multiprocessing_context: DefaultContext):
    s = multiprocessing_context.Process(
        target=server.start_server, name="ServerProcess",
    )
    s.start()


if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    # Start the main process
    main()
