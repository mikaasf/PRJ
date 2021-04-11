import numpy as np
import threading
import time
from camera import Camera


class Connector (threading.Thread):
    
    def __init__(self, cam: Camera):
        
        threading.Thread.__init__(self)
        self.__cam: Camera = cam
        self.__cam_frames: list = []
        
    
    def run(self):
        print("Start of connector thread")
        self.get_frames()
        print("End of thread")
    
    def get_frames(self):
        while True:

            self.__cam_frames = self.__cam.frames
            if len(self.__cam_frames) > 50:
                self.__cam.clear_frames()
            print("Connector array size: " + str(len(self.__cam_frames)))
            print("image mem size: %d kB" % (np.array(self.__cam_frames).nbytes // 1000))
            time.sleep(1)

            if not self.__cam.is_alive():
                print("Releasing connector...")
                break


if __name__ == '__main__':
    
    thread_lock = threading.Lock()
    
    camera = Camera(video_src=0, thread_lock=thread_lock)
    con = Connector(cam=camera)
    
    camera.start()
    con.start()
    
    camera.join()
    con.join()
    
    print("Exiting Main Thread")
