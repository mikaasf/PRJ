import cv2
import deepface.DeepFace
import numpy as np
import os
import time
import threading


class DeepFaceClassifier(threading.Thread):

    def __init__(self, id_video: str, video_path: str, insert_fun, socket):
        super().__init__()
        self.__id_video: str = id_video
        self.__socket = socket
        self.__cap = cv2.VideoCapture(video_path)
        self.__analyse_count: int = 5
        self.__counter_analized_frames: int = -1
        self.__counter_frames_to_analyse: int = -1
        self.__min_confidence: int = 80
        self.__buffer: list = list()
        self.__timestamps_emotion: list = list()
        self.__insert_fun = insert_fun
        self.__feelings_to_emotions: dict = {
            "angry": "angry",
            "fear": "afraid",
            "sad": "sad",
            "disgust": "disgusted",
            "happy": "happy",
            "surprise": "surprised"
        }
        self.__recommended_settings: float = np.round(os.path.getsize(video_path) / 4000000)
        self.__timestamp: int = 0
        print(video_path, self.__cap.isOpened(), id_video, self.__recommended_settings)

    def run(self) -> None:
        self.generate_annotations()
        self.__socket.emit("deepface_complete")

    def generate_annotations(self):
        # Check if camera opened successfully
        if not self.__cap.isOpened():
            print("Error opening video stream or file")

        previous_annot = None
        self.__timestamp = time.time()
        while self.__cap.isOpened():
            frame_exists, current_frame = self.__cap.read()

            if frame_exists:
                self.__counter_frames_to_analyse += 1
                if self.__counter_frames_to_analyse == self.__recommended_settings:
                    self.__counter_frames_to_analyse = 0
                    self.__counter_analized_frames += 1
                    try:
                        demographics = deepface.DeepFace.analyze(current_frame, actions=["emotion"],
                                                                 detector_backend='opencv')
                        dominant_emotion = demographics.get("dominant_emotion")
                        dominant_emotion_confidence = demographics['emotion'][dominant_emotion]
                        # print(dominant_emotion, dominant_emotion_confidence)
                        # if the confidence level is above the defined value then add to the buffer array
                        if dominant_emotion_confidence > self.__min_confidence:  # and dominant_emotion != 'neutral':
                            self.__buffer.append(dominant_emotion)
                            # current position of the video file in seconds
                            # print("ts", self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
                            self.__timestamps_emotion.append(self.__cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
                        # print("buffer", self.buffer)
                    except ValueError:
                        print("Face not found")
                        continue

                    if self.__counter_analized_frames > self.__analyse_count:
                        values, counts = np.unique(self.__buffer, return_counts=True)
                        # if the dominant emotion was in more than a third of the emotions in buffer
                        if len(counts) and np.max(counts) > len(self.__buffer) / 3:
                            ind = np.argmax(counts)
                            print(len(counts), values[ind])
                            if values[ind] != "neutral":
                                if previous_annot:
                                    if previous_annot[0] != self.__feelings_to_emotions.get(values[ind]):
                                        self.__insert_fun(previous_annot)
                                        previous_annot = [self.__feelings_to_emotions.get(values[ind]),
                                                          self.__timestamps_emotion[0], self.__id_video,
                                                          self.__timestamps_emotion[
                                                              len(self.__timestamps_emotion) - 1] -
                                                          self.__timestamps_emotion[0]]
                                    else:
                                        previous_annot[3] = self.__timestamps_emotion[
                                                                len(self.__timestamps_emotion) - 1] - \
                                                            self.__timestamps_emotion[0]
                                else:
                                    previous_annot = [self.__feelings_to_emotions.get(values[ind]),
                                                      self.__timestamps_emotion[0], self.__id_video,
                                                      self.__timestamps_emotion[len(self.__timestamps_emotion) - 1] -
                                                      self.__timestamps_emotion[0]]
                            else:
                                if previous_annot:
                                    self.__insert_fun(previous_annot)
                                previous_annot = None
                        else:
                            if previous_annot:
                                self.__insert_fun(previous_annot)
                            previous_annot = None

                        self.__buffer.clear()
                        self.__timestamps_emotion.clear()
                        self.__counter_analized_frames = 0
                cv2.imshow('Video' + self.__id_video, current_frame)

            else:
                self.__cap.release()
                if previous_annot:
                    self.__insert_fun(previous_annot)
                break

            key: int = cv2.waitKey(1)

            if key == 27:  # Esc
                self.__cap.release()
                cv2.destroyWindow('Video' + self.__id_video)
                break

        cv2.destroyWindow('Video' + self.__id_video)
        # print(time.time() - self.timestamp)
