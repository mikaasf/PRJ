import numpy as np
import threading
from camera_deepfaceAnalysis import Camera
from deepface import DeepFace as dF


class Connector(threading.Thread):

    def __init__(self, cam: Camera, semaphore: threading.Semaphore):
        threading.Thread.__init__(self)
        self.__semaphore: threading.Semaphore = semaphore
        self.__cam: Camera = cam
        self.__cam_frames: list = []

    def run(self):
        print("Start of connector thread")
        self.get_frames()
        print("End of thread")

    def get_frames(self):
        while True:

            if self.__cam.is_alive():
                self.__semaphore.acquire()
                self.__cam_frames = self.__cam.frames
                self.__cam.clear_frames()

                demographics = dF.analyze(self.__cam_frames, actions=["emotion"])

                print(demographics.get("dominant_emotion"))

                print("Connector array size: " + str(len(self.__cam_frames)))
                print("image mem size: %d kB" % (np.array(self.__cam_frames).nbytes // 1000))

            else:
                print("Releasing connector...")
                break


if __name__ == '__main__':
    s = threading.Semaphore(value=0)

    camera = Camera(video_src=0, semaphore=s)
    con = Connector(cam=camera, semaphore=s)

    camera.start()
    con.start()

    camera.join()
    con.join()

    print("Exiting Main Thread")
