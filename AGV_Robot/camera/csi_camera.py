from picamera2 import Picamera2
import cv2
import time
from utils.buffer import csi_frame

# === Picamera2 초기화 ===
class CSICamera:
    def __init__(self, width=640, height=480, fmt="RGB888"):
        self.picam2 = Picamera2()
        self.picam2.preview_configuration.main.size = (width, height)
        self.picam2.preview_configuration.main.format = fmt
        self.picam2.configure("preview")
        self.picam2.start()
        time.sleep(1)

        print("Picamera2 Init Complete")

    # === 표준 화면 비율 ===
    # IMX219 센서
    # 최대 해상도: 3280x2464 (약 8MP)
    # 센서 기본 비율: 4:3 (3280:2464 ≈ 1.333)
    def picam2_task(self, target_width=320, target_height=240, crop=None):
        while True:
            frame = self.picam2.capture_array()
            
            # crop을 list 혹은 tuple로 전달
            if crop is not None:
                y_start, y_end, x_start, x_end = crop
                frame = frame[y_start:y_end, x_start:x_end]
            
            frame_resized = cv2.resize(frame, (target_width, target_height))

            if not csi_frame.full():
                csi_frame.put(frame_resized)

    def picam2_stop(self):
        self.picam2.stop()

# python -m camera.csi_camera 명령어로 실행
if __name__ == "__main__":
    import threading
    
    cap = CSICamera()
    # picam2_task가 csi_frame에 영상 데이터 저장
    task_thread = threading.Thread(target=cap.picam2_task, daemon=True)
    task_thread.start()
    
    while True:
		    # csi_frame에 저장된 frame을 가져와 반전시켜 show
        frame = csi_frame.get()
        frame = cv2.flip(frame, -1)
        cv2.imshow("Video", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.picam2_stop()
    cv2.destroyAllWindows()