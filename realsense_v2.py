import numpy as np
import cv2
import threading
import pyrealsense2 as rs
import socket
from frame_segment import FrameSegment


class Camera (threading.Thread):

    def __init__(self, is_debug: bool = False, cam_device: int = 0):
        threading.Thread.__init__(self)

        # Configure color streams
        self.__pipeline: rs.pipeline = rs.pipeline()
        self.__config: rs.config = rs.config()
        self.__config.enable_stream(
            rs.stream.color, 640, 480, rs.format.rgb8, 30)
        
        self.__cam: cv2.VideoCapture = None
        self.__is_realsense_on: bool = True
        self.__cam_device: int = cam_device

        s: socket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.__fs: FrameSegment = FrameSegment(s, 5005)

        self.__isDebug: bool = is_debug

    def run(self) -> None:
        print("Start of camera thread")
        self.read_from_camera()
        print("End of camera thread")

    def read_from_camera(self) -> None:

        # Start streaming
        try:
            self.__pipeline.start(self.__config)
        except:
            self.__is_realsense_on = False
            self.__cam = cv2.VideoCapture(self.__cam_device, cv2.CAP_DSHOW)
            print('Could not detect realsense. Activating camera device')


        if self.__is_realsense_on:
            while True:

                # Wait for color frame
                frames: rs.composite_frame = self.__pipeline.wait_for_frames()
                color_frame: rs.video_frame = frames.get_color_frame()

                if color_frame:

                    # Convert images to numpy arrays
                    color_image: np.ndarray = np.asanyarray(color_frame.get_data())

                    self.__fs.send_frame(color_image)

                    # Show images
                    if self.__isDebug:
                        cv2.imshow('RealSense', cv2.cvtColor(
                            color_image, cv2.COLOR_RGB2BGR))

                key: int = cv2.waitKey(1)

                if key == 27:       # Esc
                    print("Releasing camera...")
                    cv2.destroyAllWindows()

                    # Stop streaming
                    self.__pipeline.stop()
                    break
        
        else:
            while True:

                color_image: np.ndarray
                flag, color_image = self.__cam.read()

                if flag:

                    self.__fs.send_frame(color_image)

                    # Show images
                    if self.__isDebug:
                        cv2.imshow('RealSense', color_image)

                key: int = cv2.waitKey(1)

                if key == 27:       # Esc
                    print("Releasing camera...")
                    cv2.destroyAllWindows()

                    # Stop streaming
                    self.__cam.release()
                    break


if __name__ == '__main__':
    cam = Camera(is_debug=True)
    # cam = Camera()

    cam.start()
    cam.join()

    print("Exiting Main Thread")
