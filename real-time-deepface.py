import deepface.DeepFace
import cv2
import numpy as np
import os

flag: bool
path = str(input("Indique o caminho do vídeo (path)"))
cap = cv2.VideoCapture(path)
analyse_count = 10
counter = -1
counter2 = -1
min_confidence = 50
buffer = list()
annotations = list()

recommended_settings = os.path.getsize(path) / 3000000
frame_r_analysis = int(input("Indique o intervalo de análise de emoções.\n"
                             "Considere que um menor intervalo aumenta o tempo de processamento.\n"
                             "Intervalo recomendado: " + str(int(recommended_settings))))

# Check if camera opened successfully
if not cap.isOpened():
    print("Error opening video stream or file")

while cap.isOpened():
    flag, img = cap.read()
    if flag:
        counter2 += 1
        if counter2 == frame_r_analysis:
            counter2 = 0
            demographics = None
            counter += 1
            try:
                demographics = deepface.DeepFace.analyze(img, actions=["emotion"])
                # print(demographics)
                dominant_emotion = demographics.get("dominant_emotion")
                dominant_emotion_confidence = demographics['emotion'][dominant_emotion]
                # print(dominant_emotion, dominant_emotion_confidence)
                if dominant_emotion_confidence > min_confidence and dominant_emotion != 'neutral':
                    buffer.append(dominant_emotion)
                # print("buffer", buffer)
            except ValueError:
                print("Face not found")
                continue

            if counter > analyse_count:
                values, counts = np.unique(buffer, return_counts=True)
                if len(counts) > 0:
                    ind = np.argmax(counts)
                    # print(values[ind])
                    annotations.append(values[ind])
                    buffer.clear()
                    counter = 0
                    print(annotations)
                else:
                    annotations.append('none/neutral')

            print(counter)
        cv2.imshow('Video', img)

    else:
        cap.release()
        break

    key: int = cv2.waitKey(1)

    if key == 27:  # Esc
        print("Releasing camera...")
        cap.release()
        cv2.destroyAllWindows()
        break

cv2.destroyAllWindows()
print(annotations)
