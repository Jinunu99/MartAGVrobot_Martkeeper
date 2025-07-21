import cv2
import numpy as np
import threading
import time
from camera.csi_camera import CSICamera
from utils.buffer import csi_frame

def empty(a):
    pass

class LabFilter:
    def __init__(self):
        self.window_name = "LAB Color Picker"
        self.mask_window = "Mask Window"
        self.result_window = "Result Window"

        self.l_min = 0
        self.l_max = 255
        self.a_min = 0
        self.a_max = 255
        self.b_min = 0
        self.b_max = 255

        self.setup_trackbars()

    def setup_trackbars(self):
        cv2.namedWindow("LAB")
        cv2.resizeWindow("LAB", 640, 240)

        cv2.createTrackbar("L Min", "LAB", 0, 255, empty)
        cv2.createTrackbar("L Max", "LAB", 255, 255, empty)
        cv2.createTrackbar("A Min", "LAB", 0, 255, empty)
        cv2.createTrackbar("A Max", "LAB", 255, 255, empty)
        cv2.createTrackbar("B Min", "LAB", 0, 255, empty)
        cv2.createTrackbar("B Max", "LAB", 255, 255, empty)

    def get_trackbar_values(self):
        self.l_min = cv2.getTrackbarPos("L Min", "LAB")
        self.l_max = cv2.getTrackbarPos("L Max", "LAB")
        self.a_min = cv2.getTrackbarPos("A Min", "LAB")
        self.a_max = cv2.getTrackbarPos("A Max", "LAB")
        self.b_min = cv2.getTrackbarPos("B Min", "LAB")
        self.b_max = cv2.getTrackbarPos("B Max", "LAB")

    def apply_lab_filter(self, frame):
        self.get_trackbar_values()

        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        lab = cv2.cvtColor(blurred, cv2.COLOR_BGR2Lab)

        lower = np.array([self.l_min, self.a_min, self.b_min])
        upper = np.array([self.l_max, self.a_max, self.b_max])

        mask = cv2.inRange(lab, lower, upper)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Contour-based noise removal
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) < 200:
                cv2.drawContours(mask, [cnt], -1, 0, -1)

        result = cv2.bitwise_and(frame, frame, mask=mask)
        return mask, result

    def run(self):
        print("[LabFilter] Lab Filter started")
        while True:
            if not csi_frame.empty():
                frame = csi_frame.get()
                if frame is None or not isinstance(frame, np.ndarray):
                    continue

                mask, result = self.apply_lab_filter(frame)
                cv2.imshow(self.window_name, frame)
                cv2.imshow(self.mask_window, mask)
                cv2.imshow(self.result_window, result)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == "__main__":
    cap = CSICamera()
    cap_thread = threading.Thread(target=cap.run, daemon=True)
    cap_thread.start()
    time.sleep(2)

    lab_filter = LabFilter()
    lab_filter.run()

    cap.stop()
    cv2.destroyAllWindows()
