import cv2
import deepface.DeepFace
import numpy as np
import matplotlib.pyplot as plt
import time
from sklearn.metrics import confusion_matrix
from plotMatriz import plotMatriz

ye = ["angry", "angry", "angry", "disgust", "disgust", "disgust", "disgust", "fear", "fear", "fear",
      "happy", "happy", "happy", "sad", "sad", "sad", "surprise", "surprise", "surprise"]
image_paths = ["Test images/angry/10.jpeg", "Test images/angry/11.jpeg", "Test images/angry/12.jpeg",
               "Test images/disgusted/16.png", "Test images/disgusted/17.jpeg", "Test images/disgusted/18.jpeg",
               "Test images/disgusted/19.jpeg", "Test images/fear/1.jpg", "Test images/fear/2.jpeg",
               "Test images/fear/3.jpeg", "Test images/happy/4.jpeg", "Test images/happy/5.jpeg",
               "Test images/happy/6.jpeg", "Test images/sad/7.jpeg", "Test images/sad/8.jpeg", "Test images/sad/9.jpeg",
               "Test images/surprised/13.jpeg", "Test images/surprised/14.jpeg", "Test images/surprised/15.webp"]
Y = []
conf_level = []

timestamp = time.time()

for img in image_paths:
    try:
        demographics = deepface.DeepFace.analyze(img, actions=["emotion"], detector_backend='opencv')
        dominant_emotion = demographics.get("dominant_emotion")
        Y.append(demographics.get("dominant_emotion"))
        conf_level.append(float(demographics['emotion'][dominant_emotion]))
    except ValueError:
        print(img)
        Y.append("")
        conf_level.append(0)

Y_arr = np.array(Y)
ye_arr = np.array(ye)
conf_level_arr = np.array(conf_level)
avg = np.mean(conf_level_arr[Y_arr == ye_arr])
acertos = len(conf_level_arr[Y_arr == ye_arr])
timer = time.time() - timestamp

plt.plot(Y_arr[Y_arr == ye_arr], conf_level_arr[Y_arr == ye_arr], '.')
plt.plot((np.arange(0, len(np.unique(Y_arr[Y_arr == ye_arr])), 1)), np.repeat(avg, len(np.unique(Y_arr[Y_arr == ye_arr]))), label='Média do grau de confiança')
plt.axis([None, None, 0, 100])
plt.xlabel("Emoções bem classificadas")
plt.ylabel("Grau de confiança")
plt.title("Grau de confiança para as emoções bem classificadas")
plt.legend()
plt.show()

# --------------------------------------------------------------

# y = ["sad", "sad", "sad", "sad", "sad", "sad", "sad", "sad", "neutral", "surprised", "surprised", "happy", "happy", "neutral", "neutral", "neutral", "happy", "angry", "angry", "angry", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "sad", "sad", "sad", "sad", "sad", "sad", "sad", "sad", "sad", "sad", "sad", "sad", "afraid", "afraid", "angry", "angry", "angry", "angry", "angry", "angry", "angry", "angry", "disgusted", "disgusted", "disgusted", "disgusted", "disgusted", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "happy", "neutral", "neutral", "neutral", "neutral", "neutral", "neutral", "neutral", "neutral", "neutral", "neutral", "neutral", "surprised", "surprised", "surprised", "surprised", "happy", "happy", "neutral", "neutral", "neutral", "neutral", "surprised", "surprised", "surprised", "surprised", "surprised", "surprised", "surprised", "surprised", "surprised", "surprised", "surprised"]
# ye_8rs_v4 = ['neutral', 'neutral', 'sad', 'sad', 'neutral', 'afraid', 'afraid',
#        'afraid', 'neutral', 'neutral', 'neutral', 'happy', 'neutral', 'neutral',
#        'neutral', 'neutral', 'neutral', 'neutral', 'neutral', 'happy', 'happy',
#        'happy', 'neutral', 'neutral', 'neutral', 'neutral', 'neutral',
#        'neutral', 'neutral', 'sad', 'sad', 'neutral', 'neutral',
#        'neutral', 'neutral', 'neutral', 'neutral', 'sad', 'sad',
#        'afraid', 'afraid', 'neutral', 'happy', 'afraid', 'afraid', 'sad',
#        'neutral', 'afraid', 'afraid', 'neutral', 'neutral', 'neutral',
#        'neutral', 'happy', 'happy', 'neutral', 'neutral', 'neutral',
#        'neutral', 'neutral', 'neutral', 'neutral', 'neutral', 'neutral',
#        'neutral', 'neutral', 'happy', 'happy', 'happy', 'neutral',
#        'neutral', 'neutral', 'neutral', 'neutral', 'neutral', 'neutral',
#        'neutral', 'neutral', 'neutral', 'neutral', 'neutral', 'happy',
#        'neutral', 'neutral', 'neutral', 'happy', 'neutral', 'neutral',
#        'neutral', 'neutral', 'happy', 'happy', 'neutral', 'sad',
#        'sad', 'surprised', 'surprised', 'surprised', 'afraid', 'neutral',
#        'happy', 'neutral']
#
# acertos = [y[a] == ye_8rs_v4[a] for a in range(len(y))]
# print(np.sum(acertos))
# cM = confusion_matrix(y, ye_8rs_v4, labels=["neutral", "angry", "sad", "afraid", "disgusted", "surprised", "happy"])
# print(cM)
# plotMatriz(cM, ["neutral", "angry", "sad", "afraid", "disgusted", "surprised", "happy"])
# plt.show()

# --------------------------------------------------------------

# flag: bool
# path = "static/videos/Emotions.mp4"
# cap = cv2.VideoCapture(path)
# analyse_count = [1, 2, 5]
# counter = -1
# counter2 = -1
# min_confidence = [50, 65, 75, 85, 90]
# buffer = list()
# annotations = list()
# timestamps_emotion = list()
#
# #recommended_settings = os.path.getsize(path) / 3000000
# #frame_r_analysis = int(input("Indique o intervalo de análise de emoções.\n"
#  #                            "Considere que um menor intervalo aumenta o tempo de processamento.\n"
#   #                           "Intervalo recomendado: " + str(int(recommended_settings))))
#
# frame_r_analysis = [3, 5, 11, 30]
# # Check if camera opened successfully
#
#
# if __name__ is '__main__':
#     for f in frame_r_analysis:
#         for c in min_confidence:
#             for a in analyse_count:
#
#                 if not cap.isOpened():
#                     print("Error opening video stream or file")
#
#                 while cap.isOpened():
#                     flag, img = cap.read()
#                     if flag:
#                         counter2 += 1
#                         if counter2 == f:
#                             counter2 = 0
#                             demographics = None
#                             counter += 1
#                             try:
#                                 demographics = deepface.DeepFace.analyze(img, actions=["emotion"])
#                                 # print(demographics)
#                                 dominant_emotion = demographics.get("dominant_emotion")
#                                 dominant_emotion_confidence = demographics['emotion'][dominant_emotion]
#                                 # print(dominant_emotion, dominant_emotion_confidence)
#                                 if dominant_emotion_confidence > c and dominant_emotion != 'neutral':
#                                     buffer.append(dominant_emotion)
#                                     timestamps_emotion.append(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
#
#                                 # print("buffer", buffer)
#                             except ValueError:
#                                 print("Face not found")
#                                 continue
#
#                             if counter > a:
#                                 values, counts = np.unique(buffer, return_counts=True)
#                                 if len(counts) > 0:
#                                     ind = np.argmax(counts)
#                                     # print(values[ind])
#                                     annotations.append(values[ind])
#                                     buffer.clear()
#                                 else:
#                                     annotations.append('none/neutral')
#
#                                 counter = 0
#
#                         cv2.imshow('Video', img)
#
#                     else:
#                         cap.release()
#                         break
#
#                     key: int = cv2.waitKey(1)
#
#                     if key == 27:  # Esc
#                         cap.release()
#                         cv2.destroyAllWindows()
#                         break
#
#                 cv2.destroyAllWindows()
#                 print("__________________________________")
#                 print("Min confidence:", c, "Fr analysis", f, "Analyse count", a, annotations)
#                 print(np.sum(acertos))
#                 print(confusion_matrix(y, annotations,
#                                        labels=["neutral", "angry", "sad", "afraid", "disgusted", "surprised", "happy"]))
#
