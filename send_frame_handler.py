import threading
import socket
import json
import numpy as np
import cv2
from flask_socketio import SocketIO, emit

MAX_DGRAM: int = 2 ** 16


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class SendFrame(threading.Thread):

    def __init__(self, server_socket: SocketIO):
        threading.Thread.__init__(self)
        self.__server_socket: SocketIO = server_socket
        self.__socket: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.bind(('localhost', 5005))
        
        self.__end_connection: bool = False

    def run(self) -> None:
        self.send_data()
        self.__socket.close()


    def send_data(self):
        dat: str = ""

        while not self.__end_connection:
            seg: bytes
            seg, _ = self.__socket.recvfrom(MAX_DGRAM)
            msg_raw_decoded: str = seg.decode('utf-8')
            msg: list = json.loads(msg_raw_decoded)

            if msg[0]:
                dat += msg[1]

                try:
                    self.__server_socket.emit('vid', {'image': dat})

                except cv2.error as e:
                    print("Error parsing frame", e)

                dat = ""

            else:
                dat += msg[1]

    def close_socket(self):
        self.__end_connection = True
        self.__socket.close()
