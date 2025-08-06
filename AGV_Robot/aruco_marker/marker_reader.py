import cv2
import cv2.aruco as aruco
import threading
import time

class SharedFrame:
    def __init__(self):
        self.lock = threading.Lock()
        self.frame = None

    def set(self, frame):
        with self.lock:
            self.frame = frame.copy()

    def get(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

class ArUcoReader:
    def __init__(self, dictionary_id=aruco.DICT_5X5_100, cooldown=1):
        self.aruco_dict = aruco.getPredefinedDictionary(dictionary_id)
        self.parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.aruco_dict, self.parameters)
        self.last_id = None
        self.last_time = 0
        self.cooldown = cooldown

    def scan(self, frame):
        # 카메라 프레임에서 마커 탐지
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = self.detector.detectMarkers(gray)
        now = time.time()
        result = []

        if ids is not None:
            for idx, marker_id in enumerate(ids.flatten()):
                if marker_id == self.last_id and now - self.last_time < self.cooldown:
                    continue
                self.last_id = marker_id
                self.last_time = now

                # 사각형 좌표 구하기 (중앙값 등)
                corner = corners[idx].reshape((4, 2)).astype(int)
                x_min, y_min = corner.min(axis=0)
                x_max, y_max = corner.max(axis=0)
                w_box = x_max - x_min
                h_box = y_max - y_min

                # 너무 작은 마커는 무시
                if w_box * h_box < 300:
                    continue

                # 디버그용: 감지된 마커 그리기
                cv2.polylines(frame, [corner], True, (0, 255, 0), 2)
                cv2.putText(frame, f"ID:{marker_id}", (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

                result.append({
                    "id": int(marker_id),
                    "corners": corner.tolist(),
                    "bbox": [int(x_min), int(y_min), int(w_box), int(h_box)]
                })

        return result

def aruco_thread_func(shared_frame, aruco_reader, agv_messenger):
    while True:
        frame = shared_frame.get()
        if frame is None:
            time.sleep(0.05)
            continue

        marker_results = aruco_reader.scan(frame)
        for marker in marker_results:
            # 예시: 마커 ID를 agv_messenger로 전송
            agv_messenger.send_qr_info(f"ID:{marker['id']:03d}")
        time.sleep(0.01)

# python -m aruco_marker.marker_reader
if __name__ == '__main__':
    from picamera2 import Picamera2

    picam2 = Picamera2()
    picam2.configure(
        picam2.create_video_configuration(
            main={"format": "RGB888", "size": (640, 480)},
            controls={"FrameDurationLimits": (10000, 10000)}
        )
    )
    picam2.start()

    shared_frame = SharedFrame()
    aruco_reader = ArUcoReader(dictionary_id=aruco.DICT_5X5_100, cooldown=1)

    try:
        while True:
            frame = picam2.capture_array()
            aruco_ids = aruco_reader.scan(frame)
            print(aruco_ids)  # [{'id': 3, 'corners': [...], 'bbox': [x, y, w, h]}, ...]

            cv2.imshow("ArUco Marker", frame)
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break
            # time.sleep(0.5)
    except KeyboardInterrupt:
        print("종료합니다.")
