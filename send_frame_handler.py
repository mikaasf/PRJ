import threading
import socket
import json
import numpy as np
import cv2
import base64
from flask_socketio import SocketIO, emit

MAX_DGRAM: int = 2 ** 16


class SendFrame(threading.Thread):

    def __init__(self, server_socket: SocketIO):
        threading.Thread.__init__(self)
        self.__con: tuple = ('localhost', 5005)
        self.__server_socket: SocketIO = server_socket
        self.__socket: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.bind(self.__con)
        self.__path: str = "static/videos/"
        
        self.__fourcc: int = cv2.VideoWriter_fourcc(*'MJPG')
        self.__output: cv2.VideoWriter = cv2.VideoWriter(self.__path + 'teste.avi', self.__fourcc, 25, (640, 480))
        
        self.__end_connection: bool = False
        self.__is_recording: bool = False

    def run(self) -> None:
        self.send_data()


    def send_data(self):
        video: str = ""
        audio: str = ""

        while not self.__end_connection:
            seg: bytes
            seg, _ = self.__socket.recvfrom(MAX_DGRAM)
            msg_raw_decoded: str = seg.decode('utf-8')
            msg: list = json.loads(msg_raw_decoded)

            if msg[0] and msg[2]:
                video += msg[1] if msg[1] else ""
                audio += msg[3] if msg[3] else ""

                self.__server_socket.emit('vid', {'image': video, 'audio': audio})
                
                if self.__is_recording:
                    try:
                        frame_encoded: np.ndarray = np.frombuffer(base64.b64decode(video), dtype=np.uint8)
                        frame: np.ndarray = cv2.imdecode(frame_encoded, cv2.IMREAD_UNCHANGED)
                        self.__output.write(frame)

                    except cv2.error as e:
                        print("Error parsing frame:", e)

                video = ""

            elif msg:
                video += msg[1] if msg[1] else ""
                audio += msg[3] if msg[3] else ""
        
        print('acabei de gravar')
        self.__socket.close()
        self.__output.release()

    def close_socket(self):
        print('vou fechar')
        self.__end_connection = True
        
    
    def start_recording(self):
        self.__is_recording = True
