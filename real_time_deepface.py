import threading
import deepface.DeepFace
import cv2
import numpy as np
import os


class DeepFaceClassifier(threading.Thread):
    def __init__(self, id_video, video_path, insert_fun, socket):
        super().__init__()
        self.id_video = id_video
        self.socket = socket
        self.cap = cv2.VideoCapture(video_path)
        # self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.analyse_count = 5
        self.counter = -1
        self.counter2 = -1
        self.min_confidence = 85
        self.buffer = list()
        self.timestamps_emotion = list()
        self.beginning_emotion = None
        self.end_emotion = None
        # debugging list, delete later
        self.annotations = list()
        self.insert_fun = insert_fun
        self.feelings_to_emotions = {
            "angry": "angry",
            "fear": "afraid",
            "sad": "sad",
            "disgust": "disgusted",
            "happy": "happy",
            "surprise": "surprised"
        }
        self.recommended_settings = np.round(os.path.getsize(video_path) / 3000000)
        print(video_path, self.cap.isOpened(), id_video, self.recommended_settings)

    def run(self) -> None:
        print("Start of deepface thread")
        self.generate_annotations()
        self.socket.emit("deepface_complete")
        print("End of thread")

    def generate_annotations(self):
        # Check if camera opened successfully
        if not self.cap.isOpened():
            print("Error opening video stream or file")

        previous_annot = None

        while self.cap.isOpened():
            frame_exists, current_frame = self.cap.read()

            if frame_exists:
                self.counter2 += 1
                if self.counter2 == self.recommended_settings:
                    self.counter2 = 0
                    self.counter += 1
                    try:
                        demographics = deepface.DeepFace.analyze(current_frame, actions=["emotion"], detector_backend='opencv')
                        # print(demographics)
                        dominant_emotion = demographics.get("dominant_emotion")
                        dominant_emotion_confidence = demographics['emotion'][dominant_emotion]
                        print(dominant_emotion, dominant_emotion_confidence)
                        # if the confidence level is above the defined value then add to the buffer array
                        if dominant_emotion_confidence > self.min_confidence:  # and dominant_emotion != 'neutral':
                            self.buffer.append(dominant_emotion)
                            # current position of the video file in seconds
                            print("ts", self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
                            self.timestamps_emotion.append(self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
                        print("buffer", self.buffer)
                    except ValueError:
                        print("Face not found")
                        continue

                    if self.counter > self.analyse_count:
                        # # if it is a neutral expression, remove from the buffer array
                        # if 'neutral' in self.buffer:
                        #     self.buffer.remove('neutral')
                        values, counts = np.unique(self.buffer, return_counts=True)
                        # if there is any more emotions than neutral
                        if len(counts) > 0:
                            ind = np.argmax(counts)
                            # print(values[ind])
                            if values[ind] != "neutral":
                                if previous_annot:
                                    if previous_annot[0] != self.feelings_to_emotions.get(values[ind]):
                                        self.annotations.append(values[ind])
                                        self.insert_fun(previous_annot)
                                        previous_annot = [self.feelings_to_emotions.get(values[ind]), self.timestamps_emotion[0], self.id_video, self.timestamps_emotion[len(self.timestamps_emotion) - 1] - self.timestamps_emotion[0]]
                                    else:
                                        previous_annot[3] = self.timestamps_emotion[len(self.timestamps_emotion) - 1] - self.timestamps_emotion[0]
                                else:
                                    previous_annot = [self.feelings_to_emotions.get(values[ind]),
                                                      self.timestamps_emotion[0], self.id_video,
                                                      self.timestamps_emotion[len(self.timestamps_emotion) - 1] - self.timestamps_emotion[0]]
                            self.buffer.clear()
                            self.timestamps_emotion.clear()
                            self.counter = 0
                            print("Annotations", self.annotations)
                        else:
                            self.annotations.append('none/neutral')

                    print(self.counter)
                cv2.imshow('Video' + self.id_video, current_frame)

            else:
                print("stopped")
                self.cap.release()
                if previous_annot:
                    self.insert_fun(previous_annot)
                break

            key: int = cv2.waitKey(1)

            if key == 27:  # Esc
                print("Releasing camera...")
                self.cap.release()
                cv2.destroyWindow('Video' + self.id_video)
                break

        cv2.destroyWindow('Video' + self.id_video)
        print(self.annotations)



# flag: bool
# path = str(input("Indique o caminho do vídeo (path)"))
# cap = cv2.VideoCapture(path)
# analyse_count = 10
# counter = -1
# counter2 = -1
# min_confidence = 50
# buffer = list()
# annotations = list()
#
# recommended_settings = os.path.getsize(path) / 3000000
# frame_r_analysis = int(input("Indique o intervalo de análise de emoções.\n"
#                              "Considere que um menor intervalo aumenta o tempo de processamento.\n"
#                              "Intervalo recomendado: " + str(int(recommended_settings))))
#
# # Check if camera opened successfully
# if not cap.isOpened():
#     print("Error opening video stream or file")
#
# while cap.isOpened():
#     flag, img = cap.read()
#     if flag:
#         counter2 += 1
#         if counter2 == frame_r_analysis:
#             counter2 = 0
#             demographics = None
#             counter += 1
#             try:
#                 demographics = deepface.DeepFace.analyze(img, actions=["emotion"])
#                 # print(demographics)
#                 dominant_emotion = demographics.get("dominant_emotion")
#                 dominant_emotion_confidence = demographics['emotion'][dominant_emotion]
#                 # print(dominant_emotion, dominant_emotion_confidence)
#                 if dominant_emotion_confidence > min_confidence and dominant_emotion != 'neutral':
#                     buffer.append(dominant_emotion)
#                 # print("buffer", buffer)
#             except ValueError:
#                 print("Face not found")
#                 continue
#
#             if counter > analyse_count:
#                 values, counts = np.unique(buffer, return_counts=True)
#                 if len(counts) > 0:
#                     ind = np.argmax(counts)
#                     # print(values[ind])
#                     annotations.append(values[ind])
#                     buffer.clear()
#                     counter = 0
#                     print(annotations)
#                 else:
#                     annotations.append('none/neutral')
#
#             print(counter)
#         cv2.imshow('Video', img)
#
#     else:
#         cap.release()
#         break
#
#     key: int = cv2.waitKey(1)
#
#     if key == 27:  # Esc
#         print("Releasing camera...")
#         cap.release()
#         cv2.destroyAllWindows()
#         break
#
# cv2.destroyAllWindows()
# print(annotations)
