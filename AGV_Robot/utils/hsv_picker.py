import cv2
import numpy as np
import threading
import time
from camera.csi_camera import CSICamera
from utils.buffer import csi_frame

def empty(a):
    pass

class HSVFilter:
    def __init__(self, width=680, height=480):
        # === HSV 필터 초기값 설정 ===
        self.h_min = 0
        self.h_max = 255
        self.s_min = 0
        self.s_max = 255
        self.v_min = 0
        self.v_max = 255
        
        # === 창 이름 설정 ===
        self.window_name = "HSV Color Picker"
        self.mask_window = "Mask Window"
        self.result_window = "Result WIndow"
        
        # === 트랙바 초기화 ===
        self.setup_trackbars()

    # === HSV 조정용 트랙바 설정 ===
    def setup_trackbars(self):
        cv2.namedWindow("HSV")
        cv2.resizeWindow("HSV", 640, 240)
        
        # === Hue 트랙바 (색상) ===
        cv2.createTrackbar("HUE Min", "HSV", 0, 179, empty)
        cv2.createTrackbar("HUE Max", "HSV", 179, 179, empty)
        
        # === Saturation 트랙바 (채도) ===
        cv2.createTrackbar("SAT Min", "HSV", 0, 255, empty)
        cv2.createTrackbar("SAT Max", "HSV", 255, 255, empty)
        
        # === Value 트랙바 (명도) ===
        cv2.createTrackbar("VALUE Min", "HSV", 0, 255, empty)
        cv2.createTrackbar("VALUE Max", "HSV", 255, 255, empty)

    # === HSV 필터 적용 ===
    def apply_hsv_filter(self, frame):
        # === 트랙바에서 현재 값 읽어오기 ===
        self.h_min = cv2.getTrackbarPos("HUE Min", "HSV")
        self.h_max = cv2.getTrackbarPos("HUE Max", "HSV")
        self.s_min = cv2.getTrackbarPos("SAT Min", "HSV")
        self.s_max = cv2.getTrackbarPos("SAT Max", "HSV")
        self.v_min = cv2.getTrackbarPos("VALUE Min", "HSV")
        self.v_max = cv2.getTrackbarPos("VALUE Max", "HSV")
    
        # GGaussianBlur로 노이즈 제거
        blurred = cv2.GaussianBlur(frame, (5,5), 0)
        
        # RGB를 HSV로 변환
        imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 현재 트랙바 값으로 HSV 범위 s설정
        lower = np.array([self.h_min, self.s_min, self.v_min])
        upper = np.array([self.h_max, self.s_max, self.v_max])
        
        # 마스크 생성
        mask = cv2.inRange(imgHSV, lower, upper)
        
        # === 노이즈 제거 (모폴로지 연산) ===
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) < 10:
                cv2.drawContours(mask, [cnt], -1, 0, -1)
                
        # 마스크 적용
        result = cv2.bitwise_and(frame, frame, mask=mask)
        
        return frame, mask, result

    def run(self, frame):
        try:
            # === HSV 필터 적용 ===
            original, mask, result = self.apply_hsv_filter(frame)
                        
            # === 화면 출력 ===
            cv2.imshow(self.window_name, original)
            cv2.imshow(self.mask_window, mask)
            cv2.imshow(self.result_window, result)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                return False
            
            return True

        except Exception as e:
            print(f"[HSV Picker] 오류 발생: {e}")
            return False

# === 메인 실행 코드 ===
# python -m utils.hsv_picker 명령어로 실행
if __name__ == "__main__":
    cap = CSICamera()
    cap_thread = threading.Thread(target=cap.run, daemon=True)
    cap_thread.start()
    time.sleep(2)
    
    try:
        # === HSV 필터 도구 초기화 ===
        print("[HSVFilter] Initializing HSV Filter Tool...")
        hsv_filter = HSVFilter()
        
        # === HSV 필터 태스크 시작 ===
        print("[HSVFilter] HSV Filter started")
        while True:
            # === 프레임 가져오기 ===
            if not csi_frame.empty():
                frame = csi_frame.get()
            
            # === 프레임 처리 및 종료 체크 ===
            if not hsv_filter.run(frame):
                break
        
    except KeyboardInterrupt:
        print("\n[HSVFilter] User interrupted")
        
    except Exception as e:
        print(f"[HSVFilter] System error: {e}")
    finally:
        cap.stop()
        cv2.destroyAllWindows()