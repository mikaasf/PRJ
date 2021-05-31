import cv2
import math
import base64
import json
import socket
import numpy as np


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
            
    def send_frame(self, img: np.ndarray, audio: list):
        json_payload_size: int = len(json.dumps([1, None, 1, None]))
        half_payload_size: int = (MAX_IMAGE_DGRAM + json_payload_size) // 2
        
        encoded_audio: str = base64.b64encode(b''.join(audio)).decode('utf-8')
        compress_img: bytes = cv2.imencode('.jpg', cv2.cvtColor(img, cv2.COLOR_BGR2RGB))[1].tobytes()
        frame: str = base64.b64encode(compress_img).decode('utf-8')

        video_size: int = len(frame)
        audio_size: int = len(encoded_audio)

        num_of_video_segments: int = math.ceil(video_size / half_payload_size)
        num_of_audio_segments: int = math.ceil(audio_size / half_payload_size)
        
        video_array_pos_start: int = 0
        audio_array_pos_start: int = 0

        while num_of_video_segments or num_of_audio_segments:
            
            video_total_free_space: int = half_payload_size
            audio_total_free_space: int = half_payload_size
            
            
            if num_of_audio_segments:
                if num_of_audio_segments == 1:
                    print(num_of_audio_segments, (half_payload_size - audio_size - audio_array_pos_start))
                    video_total_free_space += half_payload_size - audio_size - audio_array_pos_start
                    
                else:
                    print(num_of_audio_segments)
                    video_total_free_space += 0
                
            else:
                print(num_of_audio_segments)
                video_total_free_space += half_payload_size - len(json.dumps(None))
                
                
            if num_of_video_segments:
                if num_of_video_segments == 1:
                    print(num_of_video_segments, (half_payload_size - video_size - video_array_pos_start))
                    audio_total_free_space += half_payload_size - video_size - video_array_pos_start
                    
                else:
                    print(num_of_video_segments)
                    audio_total_free_space += 0
                
            else:
                print(num_of_video_segments)
                audio_total_free_space += half_payload_size - len(json.dumps(None))
                    
                    
            
            video_array_pos_end: int = min(video_size, video_array_pos_start + video_total_free_space)
            audio_array_pos_end: int = min(audio_size, audio_array_pos_start + audio_total_free_space)

            data: list = [1 if video_array_pos_end == video_size else 0, 
                          frame[video_array_pos_start:video_array_pos_end] if num_of_video_segments else None,
                          1 if audio_array_pos_end == audio_size else 0,
                          encoded_audio[audio_array_pos_start:audio_array_pos_end] if num_of_audio_segments else None]
            
            
            data: str = json.dumps(data)
            print("JSON payload size:", len(data))
            self.__s.sendto(bytes(data, encoding="utf-8"), (self.__addr, self.__port))
            
            video_array_pos_start = video_array_pos_end
            audio_array_pos_start = audio_array_pos_end


            if num_of_video_segments > 0:
                num_of_video_segments -= 1
                
            if num_of_audio_segments > 0:
                num_of_audio_segments -= 1