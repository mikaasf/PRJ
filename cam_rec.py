import numpy as np
import cv2

cap = cv2.VideoCapture(0)

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
out = cv2.VideoWriter('static/videos/teste.avi', fourcc=fourcc, fps=25)
# out2 = cv2.VideoWriter('teste2.mp4',fourcc, 30.0, (640,480))

while(cap.isOpened()):
    ret, frame = cap.read()
    if ret == True:

        # write the flipped frame
        out.write(frame)
        # out2.write(frame)

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

# Release everything if job is finished
cap.release()
out.release()
# out2.release()
cv2.destroyAllWindows()
