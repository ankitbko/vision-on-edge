"""This module is used to preform camera integration."""
import base64
import json
import time
import uuid
import cv2
import numpy as np
import logging
import sys
import pathlib
from websocket import ABNF

from rx import Observable, operators as op, interval
from socket_client import SocketClient


class Frame:
    def __init__(
        self,
        frame: np.ndarray,
        correlation_id: str,
    ) -> None:
        self.frame = frame
        self.correlation_id = correlation_id

class FrameProcessingRequest:
    def __init__(self, correlation_id: str, frame: np.ndarray) -> None:
        self.frame = frame
        self.correlation_id = correlation_id


def encode_image(image: bytes) -> str:
    """
    Encode image to base64 string.

    @param
        image (bytes): Image data in bytes
    @return
        image_str (str:) Base64 encoded image string
    """
    image = cv2.imencode(".jpg", image)[1].tobytes()
    image = base64.b64encode(image).decode("utf-8")
    return image


class FrameProvider:
    """
    Intergrate with camera, read frames and emit frame to the WebAppAPI and Queue, controlled by FPS
    """

    def __init__(self, queue) -> None:
        """
        Initialize the camera integration.

        @param
            queue (ProcessQueue): Queue to add frames to
        """
        self.queue = queue
        self.logger = logging.getLogger(
           FrameProvider.__name__,
        )
        self.ws = None
        self.vid = None

        self.ws_url = "ws://localhost:7001/ws/frame_internal"
        self.camera_path = f"{pathlib.Path(__file__).parent.resolve()}/slow_traffic_small.mp4"
        self.frame_rate_camera = 30
        self.frame_rate_ui = 15
        self.frame_rate_queue = 5
        self.frame_size_ui = (640,480)
        self.frame_size_queue = (640,480)

    def _get_camera(self, camera_path: str) -> cv2.VideoCapture:
        """
        Get camera.

        @param
            camera_path (str): Path to camera
        @return
            camera_object (cv2.VideoCapture): cv2 camera object
        """
        try:
            vid = cv2.VideoCapture(camera_path)
            return vid
        except Exception as ex:
            self.logger.exception(ex)
            self.logger.error(f"Error opening video stream {ex}")
            raise ex

    def _get_frame_stream(self, frame_rate: float) -> Observable:
        """
        Get frame stream.

        @param
            frame_rate (float): Frame rate for ui
        @return
            frame_stream (Observable): Frame stream object
        """
        frame_stream = interval(frame_rate).pipe(
            op.map(lambda _: self.vid.read()),  # read frame
            op.do_action(lambda result: self.vid.set(cv2.CAP_PROP_POS_FRAMES, 0) if result[0] is False else None), # restart video on completion
            op.filter(
                lambda result: result[0] is True and result[1] is not None
            ),  # filter None frames
            op.map(lambda result: result[1]),  # get frame
            op.map(
                lambda frame: Frame(
                    frame=frame,
                    correlation_id=str(uuid.uuid4()),
                )
            ),  # create frame object
            op.share(),  # share frame stream
        )
        return frame_stream

    def _emit_frame_to_queue(
        self, frame_stream: Observable, queue_fps: float, frame_size: list
    ) -> Observable:
        """
        Emit frame to queue.

        @param
            frame_stream (Observable): Frame stream object
            queue_fps (float): Frame rate for queue
            frame_size (list): Frame size for queue (width, height)
        @return
            frame_stream (Observable): Frame stream object
        """
        return frame_stream.pipe(
            op.sample(queue_fps),
            op.map(
                lambda frame: Frame(
                    cv2.resize(frame.frame, frame_size),
                    frame.correlation_id,
                )
            ),
            op.map(lambda frame: self._write_to_queue(frame=frame)),
        )

    def _write_to_queue(self, frame: Frame) -> bool:
        """
        Write frame to queue.

        @param
            frame (bytes): Frame to send to queue
        @return
            result (bool): Result of writing frame to queue, True for success
        """
        try:
            label_extraction_request = FrameProcessingRequest(
                correlation_id=frame.correlation_id,
                frame=frame.frame,
            )
            return self.queue.add_item(label_extraction_request)
        except Exception as ex:
            self.logger.exception(ex)
            self.logger.error(f"Error reading video stream {ex}")
            return False

    def _connect_to_socket(self) -> None:
        """
        Connect to socket.
        """
        self.ws = SocketClient(
            self.ws_url
        ) 
        self.ws.connect()
        self.ws.start_dispatcher()

    def _emit_frame_to_socket(
        self, frame_stream: Observable, socket_fps: float, frame_size: list
    ) -> Observable:
        """
        Emit frame to socket.

        @param
            frame_stream (Observable): Frame stream object
            frame_size (list): Frame size for socket (width, height)
        @return
            frame_stream (Observable): Frame stream object
        """
        return frame_stream.pipe(
            op.sample(socket_fps),
            op.map(
                lambda frame: Frame(
                    cv2.resize(frame.frame, frame_size),
                    frame.correlation_id,
                )
            ),
            op.map(
                lambda frame: Frame(
                    frame.frame,
                    frame.correlation_id,
                )
            ),
            op.map(lambda frame: self._write_to_socket(frame=frame)),
        )

    def _write_to_socket(self, frame: Frame) -> bool:
        """
        Write frame to socket.

        @param
            frame (str): Frame to send to socket
        @return
            result (bool): Result of writing frame to socket, True for success
        """
        try:
            return self.ws.send(
                json.dumps(
                    {
                        "frame": encode_image(frame.frame),
                        "correlation_id": frame.correlation_id,
                    }
                ),
                ABNF.OPCODE_BINARY,
            )
        except Exception as ex:
            self.logger.exception(ex)
            self.logger.error(f"Error writting video stream to socket {ex}")
            return False

    def start_camera(self) -> None:
        """
        Start camera in infinite loop.
        """
        self._connect_to_socket()
        self.vid = self._get_camera(self.camera_path)
        self.logger.info("Started camera...")

        frame_stream = self._get_frame_stream(1 / self.frame_rate_camera)

        socket_result_stream = self._emit_frame_to_socket(
            frame_stream, 1 / self.frame_rate_ui, self.frame_size_ui
        )
        queue_result_stream = self._emit_frame_to_queue(
            frame_stream, 1 / self.frame_rate_queue, self.frame_size_queue
        )
        socket_result_stream.subscribe(
            on_next=lambda _: None,
            on_error=lambda ex: self.logger.exception(ex),
            on_completed=lambda: self.logger.info("Completed frame stream"),
        )
        queue_result_stream.subscribe(
            on_next=lambda _: None,
            on_error=lambda ex: self.logger.exception(ex),
            on_completed=lambda: self.logger.info("Completed frame stream"),
        )
        self.logger.info("Started camera stream...")
        while True:
            if not self.vid.isOpened():
                self.logger.error("Could not open video device, reconnecting to camera")
                self.vid = self._get_camera(self.camera_path)

            time.sleep(10)

def run(queue):
    FrameProvider(queue).start_camera()