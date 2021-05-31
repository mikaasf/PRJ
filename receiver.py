import json
import socket
import cv2
import base64
import numpy as np

MAX_DGRAM: int = 2 ** 16


def main() -> None:
    """ Getting image udp frame &
    concate before decode and output image """

    # Set up socket
    s: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('193.236.162.18', 5000))
    dat: str = ""

    while True:
        seg: bytes
        seg, _ = s.recvfrom(MAX_DGRAM)
        msg_raw_decoded: str = seg.decode('utf-8')
        msg: list = json.loads(msg_raw_decoded)

        if msg[0]:
            dat += msg[1]

            try:
                img_encoded: np.ndarray = np.frombuffer(base64.b64decode(dat), dtype=np.uint8)
                img: np.ndarray = cv2.imdecode(img_encoded, cv2.IMREAD_UNCHANGED)

                cv2.imshow('frame', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            except Exception:
                print("Error parsing frame")

            dat = ""

        else:
            dat += msg[1]

    dat = ""
    s.close()


if __name__ == '__main__':
    main()
