import base64
import cv2
import json
import numpy as np
import os
import platform
import pyaudio
import threading
import socket
import subprocess
import wave
from flask_socketio import SocketIO, emit
from time import time

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WAV_OUTPUT_FILENAME = "temp.wav"
MAX_DGRAM: int = 2 ** 16
FFMPEG_LOCATION: str

if platform.system() == "Windows":
    FFMPEG_LOCATION = "C://ffmpeg//bin//ffmpeg"

elif platform.system() == "Darwin":
    FFMPEG_LOCATION = "Mac...."
    


class SendFrame(threading.Thread):

    def __init__(self, server_socket: SocketIO):
        threading.Thread.__init__(self)

        # IP port ID
        self.__con: tuple = ('localhost', 5005)

        # Websocket reference
        self.__server_socket: SocketIO = server_socket

        # Socket to recieve from camera client
        self.__socket: socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.bind(self.__con)

        # filenames and paths
        self.__videos_path: str = "static/videos/"
        self.__temp_path: str = "static/temp/"

        # PyAudio object
        self.__p = pyaudio.PyAudio()

        # Video record config
        self.__fourcc: int = cv2.VideoWriter_fourcc(*'MJPG')

        # OpenCV objects to record the received frames
        self.__rec_output: cv2.VideoWriter = cv2.VideoWriter(
            self.__temp_path + 'temp.mkv', self.__fourcc, 25, (640, 480))

        # Bool to control the thread lifetime
        self.__end_connection: bool = False

        # Bool to control the record
        self.__is_recording: bool = False

        # Auxiliary attributes for video re-encoding
        self.__start_time: float = 0.
        self.__finish_time: float = 0.
        self.__frame_counts: int = 0

        # Buffer to record audio
        self.__audio_frames: list = []

    def send_data(self):
        
        # Variables to store data
        video: str = ""
        audio: str = ""

        while not self.__end_connection:
            
            # Receive and decode data
            seg: bytes
            seg, _ = self.__socket.recvfrom(MAX_DGRAM)
            msg_raw_decoded: str = seg.decode('utf-8')
            msg: list = json.loads(msg_raw_decoded)

            if msg[0] and msg[2]:
                video += msg[1]
                audio += msg[3]

                if len(video):
                    
                    # Convert frame from text to binary
                    try:
                        frame_encoded: np.ndarray = np.frombuffer(
                            base64.b64decode(video.encode('utf-8')), dtype=np.uint8)
                        frame: np.ndarray = cv2.imdecode(
                            frame_encoded, cv2.IMREAD_UNCHANGED)
                        
                        # Retransmit frame
                        self.__server_socket.emit('vid', {'video': video})

                        # Write frame into buffer
                        if self.__is_recording:
                            self.__rec_output.write(frame)
                            self.__frame_counts += 1

                    except Exception as e:
                        print("Error parsing frame:", e)

                if len(audio):
                    
                    # Convert audio from text to binary
                    encoded_audio: str = base64.b64decode(
                        audio.encode('utf-8'))

                    # Write audio into buffer
                    if self.__is_recording:
                        self.__audio_frames.append(encoded_audio)
                        

                video = ""
                audio = ""

            elif msg:
                video += msg[1]
                audio += msg[3]


        if self.__is_recording:
            
            # End of recording timestamp
            self.__finish_time = time()
            
            # Delete temporary files
            if os.path.exists(self.__temp_path + "unknown.mkv"):
                os.remove(self.__temp_path + "unknown.mkv")

            if os.path.exists(self.__temp_path + WAV_OUTPUT_FILENAME):
                os.remove(self.__temp_path + WAV_OUTPUT_FILENAME)

            if os.path.exists(self.__videos_path + "unknown.mp4"):
                os.remove(self.__videos_path + "unknown.mp4")

            # Inicialize audio recorder
            wf = wave.open(self.__temp_path + WAV_OUTPUT_FILENAME, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.__p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.__audio_frames))

            # Close recorder objects
            wf.close()
            self.__rec_output.release()

            # Calculate real framerate
            elapsed_time = self.__finish_time - self.__start_time
            recorded_fps = self.__frame_counts / elapsed_time
            
            # Remux recorded video
            if abs(recorded_fps - 25) >= .01:
                cmd = FFMPEG_LOCATION + " -r " + \
                    str(recorded_fps) + " -i " + self.__temp_path + \
                    "temp.mkv -pix_fmt yuv420p -r 25 " + self.__temp_path + "unknown.mkv -loglevel quiet"
                subprocess.call(cmd, shell=True)

                cmd = FFMPEG_LOCATION + " -ac 2 -channel_layout stereo -i " + self.__temp_path + \
                    WAV_OUTPUT_FILENAME + " -i " + self.__temp_path + "unknown.mkv -pix_fmt yuv420p " + \
                    self.__videos_path + "unknown.mp4 -loglevel quiet"
                subprocess.call(cmd, shell=True)

            # Mux recorded video
            else:
                cmd = FFMPEG_LOCATION + " -ac 2 -channel_layout stereo -i " + self.__temp_path + \
                    WAV_OUTPUT_FILENAME + " -i " + self.__temp_path + \
                    "teste.mkv -pix_fmt yuv420p " + self.__videos_path + "unknown.mp4 -loglevel quiet"
                subprocess.call(cmd, shell=True)
        
        # Close socket and end thread lifecycle
        self.__socket.close()

    def close_socket(self) -> None:
        self.__end_connection = True

    def start_recording(self) -> None:
        self.__start_time = time()
        self.__is_recording = True

    def run(self) -> None:
        self.send_data()
