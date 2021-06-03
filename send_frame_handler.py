import os
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
WAV_OUTPUT_FILENAME = "output.wav"
MAX_DGRAM: int = 2 ** 16


class SendFrame(threading.Thread):

    def __init__(self, server_socket: SocketIO):
        threading.Thread.__init__(self)

        # IP port ID
        self.__con: tuple = ('localhost', 5005)

        # Websocket reference
        self.__server_socket: SocketIO = server_socket

        # Socket to recieve from camera
        self.__socket: socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.bind(self.__con)

        # filenames and paths
        self.__temp_path: str = "static/temp/"
        self.__videos_path: str = "static/videos/"
        self.__stream_rec_vid_filename: str = "stream_video.mkv"
        self.__stream_rec_aud_filename: str = "stream_audio.wav"

        # PyAudio object
        self.__p = pyaudio.PyAudio()

        # Video record config
        self.__fourcc: int = cv2.VideoWriter_fourcc(*'MJPG')

        # OpenCV objects to record the received frames
        self.__rec_output: cv2.VideoWriter = cv2.VideoWriter(
            self.__temp_path + 'teste.mkv', self.__fourcc, 25, (640, 480))

        self.__stream_output: cv2.VideoWriter = cv2.VideoWriter(
            self.__temp_path + self.__stream_rec_vid_filename, self.__fourcc, 25, (640, 480))

        # Bool to control the thread lifetime
        self.__end_connection: bool = False

        # Bool to control the record
        self.__is_recording: bool = False

        # Auxiliary attributes for video re-encoding
        self.__start_time: float = 0.
        self.__frame_counts: int = 0

        # Buffer to record audio
        self.__audio_frames: list = []

    def send_data(self):

        video: str = ""
        audio: str = ""

        while not self.__end_connection:
            wf_temp = wave.open(self.__temp_path +
                                self.__stream_rec_aud_filename, 'wb')
            wf_temp.setnchannels(CHANNELS)
            wf_temp.setsampwidth(self.__p.get_sample_size(FORMAT))
            wf_temp.setframerate(RATE)

            seg: bytes
            seg, _ = self.__socket.recvfrom(MAX_DGRAM)
            msg_raw_decoded: str = seg.decode('utf-8')
            msg: list = json.loads(msg_raw_decoded)

            if msg[0] and msg[2]:
                video += msg[1]
                audio += msg[3]

                if len(video):
                    try:
                        frame_encoded: np.ndarray = np.frombuffer(
                            base64.b64decode(video.encode('utf-8')), dtype=np.uint8)
                        frame: np.ndarray = cv2.imdecode(
                            frame_encoded, cv2.IMREAD_UNCHANGED)

                        if not self.__stream_output.isOpened():
                            self.__stream_output.open(self.__temp_path + self.__stream_rec_vid_filename,
                                                      self.__fourcc, 25, (640, 480))

                        self.__stream_output.write(frame)
                        self.__stream_output.release()

                        if self.__is_recording:
                            self.__rec_output.write(frame)
                            self.__frame_counts += 1

                    except Exception as e:
                        print("Error parsing frame:", e)

                if len(audio):
                    encoded_audio: str = base64.b64decode(
                        audio.encode('utf-8'))
                    wf_temp.writeframes(encoded_audio)
                    wf_temp.close()

                    if self.__is_recording:
                        self.__audio_frames.append(encoded_audio)
                        
                if os.path.exists(self.__temp_path + "stream.mp4"):
                    os.remove(self.__temp_path + "stream.mp4")

                cmd = "C://ffmpeg//bin//ffmpeg -ac 2 -channel_layout stereo -i " + self.__temp_path + \
                    "stream_audio.wav -i " + self.__temp_path + \
                    "stream_video.mkv -pix_fmt yuv420p " + self.__temp_path + "stream.mp4 -loglevel quiet"
                subprocess.call(cmd)
                
                try:
                    stream_bits: bytes = open(self.__temp_path + "stream.mp4", "rb").read()
                    print(len(stream_bits))
                    video_to_send: str = base64.b64encode(stream_bits).decode('utf-8')
                    self.__server_socket.emit('vid', {'video': video_to_send})
                except Exception as e:
                    print(e)

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

        print('end of stream')

        if self.__is_recording:
            if os.path.exists(self.__temp_path + "teste2.mkv"):
                os.remove(self.__temp_path + "teste2.mkv")

            if os.path.exists(self.__temp_path + WAV_OUTPUT_FILENAME):
                os.remove(self.__temp_path + WAV_OUTPUT_FILENAME)

            if os.path.exists(self.__videos_path + "final_output.mp4"):
                os.remove(self.__videos_path + "final_output.mp4")

            wf = wave.open(self.__temp_path + WAV_OUTPUT_FILENAME, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.__p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.__audio_frames))

            wf.close()
            self.__rec_output.release()

            elapsed_time = time() - self.__start_time
            recorded_fps = self.__frame_counts / elapsed_time

            print("total frames " + str(self.__frame_counts))
            print("elapsed time " + str(elapsed_time))
            print("recorded fps " + str(recorded_fps))

            if abs(recorded_fps - 25) >= .01:
                cmd = "C://ffmpeg//bin//ffmpeg -r " + \
                    str(recorded_fps) + " -i " + self.__temp_path + \
                    "teste.mkv -pix_fmt yuv420p -r 25 " + self.__temp_path + "teste2.mkv -loglevel quiet"
                subprocess.call(cmd, shell=True)

                cmd = "C://ffmpeg//bin//ffmpeg -ac 2 -channel_layout stereo -i " + self.__temp_path + \
                    "output.wav -i " + self.__temp_path + "teste2.mkv -pix_fmt yuv420p " + \
                    self.__videos_path + "final_output.mp4 -loglevel quiet"
                subprocess.call(cmd, shell=True)

            else:
                cmd = "C://ffmpeg//bin//ffmpeg -ac 2 -channel_layout stereo -i " + self.__temp_path + \
                    "output.wav -i " + self.__temp_path + \
                    "teste.mkv -pix_fmt yuv420p " + self.__videos_path + "final_output.mp4 -loglevel quiet"
                subprocess.call(cmd, shell=True)

        self.__socket.close()
        self.__rec_output.release()

    def close_socket(self):
        print('vou fechar')
        self.__end_connection = True

    def start_recording(self):
        self.__start_time = time()
        self.__is_recording = True

    def run(self) -> None:
        self.send_data()
