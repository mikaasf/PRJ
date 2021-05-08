"""
 @author from: https://medium.com/@fromtheast/fast-camera-live-streaming-with-udp-opencv-de2f84c73562
 @adapted by: Micaela Franco and Miguel Peixoto
 """

import cv2
import math
import base64
import json
import socket


MAX_DGRAM: int = 2**16
MAX_IMAGE_DGRAM: int = MAX_DGRAM - 64  # minus 64 bytes in case UDP frame overflown


class FrameSegment(object):
    """
    Object to break down image frame segment
    if the size of image exceed maximum datagram size
    """

    def __init__(self, sock, port, addr="127.0.0.1"):
        self.__s: socket = sock
        self.__port: int = port
        self.__addr: str = addr                    
            
    def send_frame(self, img):
        json_payload_size: int = len(json.dumps([1, None]))
        
        compress_img: bytes = cv2.imencode('.jpg', cv2.cvtColor(img, cv2.COLOR_BGR2RGB))[1].tobytes()
        frame: str = base64.b64encode(compress_img).decode('utf-8')

        size: int = len(frame)

        num_of_segments: int = math.ceil(size / (MAX_IMAGE_DGRAM + json_payload_size))
        array_pos_start: int = 0

        while num_of_segments:
            array_pos_end: int = min(size, array_pos_start + (MAX_IMAGE_DGRAM - json_payload_size))

            data: list = [1 if array_pos_end == size else 0, frame[array_pos_start:array_pos_end]]
            data: str = json.dumps(data)

            self.__s.sendto(bytes(data, encoding="utf-8"), (self.__addr, self.__port))
            array_pos_start = array_pos_end

            num_of_segments -= 1