from datetime import datetime
import numpy as np
from PIL import Image
import onnxruntime

import sys
import pathlib
sys.path.append(f"{pathlib.Path(__file__).absolute().parent.parent.resolve()}/common")

import time
import logging
import os
import signal
from typing import Any

# this function is from yolo3.utils.letterbox_image
def letterbox_image(image, size):
    '''resize image with unchanged aspect ratio using padding'''
    iw, ih = image.size
    w, h = size
    scale = min(w/iw, h/ih)
    nw = int(iw*scale)
    nh = int(ih*scale)

    image = image.resize((nw,nh), Image.BICUBIC)
    new_image = Image.new('RGB', size, (128,128,128))
    new_image.paste(image, ((w-nw)//2, (h-nh)//2))
    return new_image

def preprocess(img):
    model_image_size = (416, 416)
    boxed_image = letterbox_image(img, tuple(reversed(model_image_size)))
    image_data = np.array(boxed_image, dtype='float32')
    image_data /= 255.
    image_data = np.transpose(image_data, [2, 0, 1])
    image_data = np.expand_dims(image_data, 0)
    return image_data

def infer(frame):
    image = Image.fromarray(frame)

    # input
    image_data = preprocess(image)
    image_size = np.array([image.size[1], image.size[0]], dtype=np.float32).reshape(1, 2)

    session = onnxruntime.InferenceSession(f'{pathlib.Path(__file__).parent.resolve()}/tiny-yolov3-11.onnx')

    boxes, scores, indices = session.run(['yolonms_layer_1', 'yolonms_layer_1:1', 'yolonms_layer_1:2'], {'input_1': image_data, 'image_shape': image_size})

    out_boxes, out_scores, out_classes = [], [], []
    for idx_ in indices[0]:
        out_classes.append(idx_[1])
        out_scores.append(scores[tuple(idx_)])
        idx_1 = (idx_[0], idx_[2])
        out_boxes.append(boxes[idx_1])

    #print(max(out_scores), out_classes[out_scores.index(max(out_scores))])

class FrameProcessor:
    """
    Process two.
    """

    def __init__(self) -> None:
        """
        Initialize the process two.
        """
        pass

    def run(self, queue) -> None:
        """
        Run the process two.

        @param
            queue: ProcessQueue object to communicate within processes
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting process two...")
        while True:
            if not queue.is_empty():
                item = queue.get_item()
                self._process(item)
            else:
                # Check for item in queue every 100 milliseconds
                time.sleep(0.1)

    def _process(self, item: Any) -> None:
        """
        Process two processing.

        @param
            item: Object to be processed
        """
        try:
            self.logger.info(f"Received in process two: {item.correlation_id}")
            start = datetime.now().timestamp()
            infer(item.frame)
            end = datetime.now().timestamp()
            self.logger.info(f'Time taken for inference: {end-start}')
            # Perform CPU bound task
            # time.sleep(0.2)
            # for _ in range(2):
            #     # arithmetic operation to create CPU load
            #     math.factorial(1000000)
        except Exception as e:
            # Kill the main process in case of error
            self.logger.critical("Failed to start the process two {}".format(e))
            self.logger.exception(e)
            self.logger.critical(f"Killing main process... pid = {os.getppid()}")
            os.kill(os.getppid(), signal.SIGTERM)
