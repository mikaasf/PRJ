import deepface.DeepFace
from deepface import DeepFace
import numpy as np
import cv2

flag: bool
cam = cv2.VideoCapture(0)

while True:

    flag, img = cam.read()
    demographics = deepface.DeepFace.analyze(img, actions=["emotion"])

    if flag:
        cv2.imshow('Video', img)
        print(demographics.get("dominant_emotion"))

    key: int = cv2.waitKey(1)
    if key == 27:  # Esc
        print("Releasing camera...")
        cv2.destroyAllWindows()
        break
