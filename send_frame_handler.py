import threading
import socket
import json
from time import time
import numpy as np
import cv2
import base64
from flask_socketio import SocketIO, emit
import subprocess
import pyaudio
import wave

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WAVE_OUTPUT_FILENAME = "output.wav"
MAX_DGRAM: int = 2 ** 16


class SendFrame(threading.Thread):

    def __init__(self, server_socket: SocketIO):
        threading.Thread.__init__(self)
        self.__con: tuple = ('localhost', 5005)
        self.__server_socket: SocketIO = server_socket
        self.__socket: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.bind(self.__con)
        self.__path: str = "static/temp/"
        
        self.__p = pyaudio.PyAudio()
        
        self.__fourcc: int = cv2.VideoWriter_fourcc(*'MJPG')
        self.__output: cv2.VideoWriter = cv2.VideoWriter(self.__path + 'teste.mkv', self.__fourcc, 25, (640, 480))
        
        self.__end_connection: bool = False
        self.__is_recording: bool = False
        
        self.__start_time: float = 0.
        self.__frame_counts: int = 0

    def run(self) -> None:
        self.send_data()


    def send_data(self):
        wf = wave.open( self.__path + WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.__p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        
        
        video: str = ""
        audio: str = ""
        
        self.__start_time = time()
        while not self.__end_connection:
            seg: bytes
            seg, _ = self.__socket.recvfrom(MAX_DGRAM)
            msg_raw_decoded: str = seg.decode('utf-8')
            msg: list = json.loads(msg_raw_decoded)

            if msg[0] and msg[2]:
                video += msg[1]
                audio += msg[3]
                
                
                # if not self.__output.isOpened():
                #     self.__output.open(self.__path + 'teste.avi', self.__fourcc, 25, (640, 480))
                
                if len(video):
                    try:
                        frame_encoded: np.ndarray = np.frombuffer(base64.b64decode(video.encode('utf-8')), dtype=np.uint8)
                        frame: np.ndarray = cv2.imdecode(frame_encoded, cv2.IMREAD_UNCHANGED)
                        self.__output.write(frame)
                        self.__frame_counts += 1
                        
                    except cv2.error as e:
                        print("Error parsing frame:", e)
                
                
                if len(audio):
                    wf.writeframes(base64.b64decode(audio.encode('utf-8')))
                
                video = ""
                audio = ""
                    
                # cmd = "ffmpeg -ac 2 -channel_layout stereo -i static/temp/output.wav -i static/temp/teste.avi -pix_fmt yuv420p static/videos/final_output.avi"
                # subprocess.call(cmd, shell=True)
                
                # print(len(video))
                # print(len(audio))

                # self.__server_socket.emit('vid', {'image': video.encode('utf-8'), 'audio': audio})
                # self.__server_socket.emit('vid', {'image': video})
                
                # if self.__is_recording:
                #     try:
                #         frame_encoded: np.ndarray = np.frombuffer(base64.b64decode(video), dtype=np.uint8)
                #         frame: np.ndarray = cv2.imdecode(frame_encoded, cv2.IMREAD_UNCHANGED)
                #         self.__output.write(frame)
                #         self

                #     except cv2.error as e:
                #         print("Error parsing frame:", e)
                        

            elif msg:
                video += msg[1]
                audio += msg[3]
        
        print('acabei de gravar')
        
        wf.close()
        self.__output.release()
        
        elapsed_time = time() - self.__start_time
        recorded_fps = self.__frame_counts / elapsed_time
        
        
        if abs(recorded_fps - 25) >= .01:
            cmd = "C://ffmpeg//bin//ffmpeg -r " + str(recorded_fps) + " -i static/temp/teste.mkv -pix_fmt yuv420p -r 25 static/temp/teste2.mkv"
            subprocess.call(cmd, shell=True)
        
            cmd = "C://ffmpeg//bin//ffmpeg -ac 2 -channel_layout stereo -i static/temp/output.wav -i static/temp/teste2.mkv -pix_fmt yuv420p static/videos/final_output.mp4"
            subprocess.call(cmd, shell=True)
            
        else:
            cmd = "C://ffmpeg//bin//ffmpeg -ac 2 -channel_layout stereo -i static/temp/output.wav -i static/temp/teste.mkv -pix_fmt yuv420p static/videos/final_output.mp4"
            subprocess.call(cmd, shell=True)
            
        self.__socket.close()
        self.__output.release()

    def close_socket(self):
        print('vou fechar')
        self.__end_connection = True
        
    
    def start_recording(self):
        self.__is_recording = True
