import cv2
from utils.buffer import usb_frame

# 지원하는 해상도 명령어 : v4l2-ctl --device=/dev/video0 --list-formats-ext
# MJPG (압축된 고속 모드) : 고해상도 + 고프레임 지원
# YUYV (비압축, 고품질 포맷) : 화질이 일정함. 다만 프레임 속도는 낮음.
class USBWebcam:
    def __init__(self, device_index=0, width=320, height=240, fmt='MJPG'):
        self.cap = cv2.VideoCapture(device_index)
        if not self.cap.isOpened():
            print("Failed to open the webcam.")
            exit()

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fmt))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        print("Webcam successfully opened.")
    
    def webcam_task(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read a frame from the webcam.")
                break
            
            frame_resized = cv2.resize(frame, (320, 240))
        
            if not usb_frame.full():
                usb_frame.put(frame_resized)
                
# python -m camera.webcam 명령어로 실행
if __name__=="__main__":
    import threading
    
    # 0번 장치는 기본 웹캠 (보통 첫 번째 연결된 USB 카메라)
    # 현재 연결된 디바이스 목록 확인 : v4l2-ctl --list-devices
    cap = USBWebcam(device_index=2)
    # webcam_task가 usb_frame에 영상 데이터 저장
    task_thread = threading.Thread(target=cap.webcam_task, daemon=True)
    task_thread.start()
    
    while True:
        # usb_frame에 저장된 frame을 가져와 반전시켜 show
        frame = usb_frame.get()
        cv2.imshow("Video", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    self.picam2.stop()
    cv2.destroyAllWindows()
        