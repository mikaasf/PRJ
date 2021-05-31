import numpy as np
import cv2
import time
import threading


class Camera(threading.Thread):

    def __init__(self, video_src: int, thread_lock: threading.Lock, frame_rate: int = 30):
        threading.Thread.__init__(self)

        self.__cam: cv2.VideoCapture = cv2.VideoCapture(video_src, cv2.CAP_DSHOW)
        self.__frame_rate: int = frame_rate
        self.__prev: float = 0.
        self.__thread_lock: threading.Lock = thread_lock

        self.__frames: list = []

    def run(self) -> None:
        print("Start of camera thread")
        self.capture_video()
        print("End of thread")

    def capture_video(self) -> None:
        while True:
            time_elapsed: float = time.time() - self.__prev

            flag: bool
            img: np.ndarray
            flag, img = self.__cam.read()

            if time_elapsed > 1. / self.__frame_rate:

                self.__prev = time.time()

                self.__thread_lock.acquire()
                self.__frames.append(img)
                # print("Camera array size: " + str(len(self.__frames)))
                self.__thread_lock.release()

                if flag:
                    cv2.imshow('Video', img)

            key: int = cv2.waitKey(1)
            if key == 27:  # Esc
                print("Releasing camera...")
                cv2.destroyAllWindows()
                self.__cam.release()
                break

    @property
    def frames(self) -> list:
        return self.__frames

    def clear_frames(self) -> None:
        self.__frames = []


if __name__ == '__main__':
    thread_lock = threading.Lock()
    camera = Camera(video_src=0, thread_lock=thread_lock)
    camera.start()

    camera.join()
    print("Exiting Main Thread")
