
from pyzbar.pyzbar import decode
import cv2
import time
import re  # 좌표 추출을 위한 정규식 사용
import json
import threading
# from utils.buffer import tx_queue  # UART 전송 큐 사용
import paho.mqtt.client as mqtt

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
        

class QRReader:
    def __init__(self, cooldown=1):
        self.last_id = None
        self.last_time = 0
        self.cooldown = cooldown

    def scan(self, frame):
        # h, w = frame.shape[:2]
        # y1 = int(h * 2 / 3)
        # roi = frame[y1:, :]  # 하단 1/3
        # roi_h, roi_w = roi.shape[:2]
        # small = cv2.resize(roi, (320, 80))  # downscale
        # scale_x = roi_w / 320
        # scale_y = roi_h / 80
        frame = cv2.convertScaleAbs(cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY), alpha=1.3, beta=20)
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)  # 다시 RGB로

        small = cv2.resize(frame, (320, 240))   # 320 240
        scale_x = frame.shape[1] / 320          # 320
        scale_y = frame.shape[0] / 240          # 240

        decoded = decode(small)
        now = time.time()
        result = []

        for obj in decoded:
            qr_results = obj.data.decode()
            if qr_results == self.last_id and now - self.last_time < self.cooldown:
                continue
            self.last_id = qr_results
            self.last_time = now

            parsed_qr = {
                "raw": qr_results,
                "id": None
            }

            try:
                match = re.search(r"ID:(\d+)", qr_results)
                if match:
                    parsed_qr["id"] = f"ID:{match.group(1)}"
            except Exception as e:
                print(f"[QRReader] 좌표 파싱 실패: {e}")

            # 1️⃣ small 기준 좌표 → roi 기준 → frame 기준으로 변환!
            x, y, w_box, h_box = obj.rect
            x = int(x * scale_x)
            y = int(y * scale_y)
            w_box = int(w_box * scale_x)
            h_box = int(h_box * scale_y)
            # roi는 frame[y1:, :] → y1만큼 y좌표를 더해줘야 함
            #y += y1

            # (선택) QR 너무 작으면 무시
            # if w_box * h_box < 100:
            #     continue

            cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), (0, 255, 0), 2)
            cv2.putText(frame, qr_results, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            result.append(parsed_qr)

        return result

def qr_thread_func(shared_frame, qr_reader, agv_messenger):
    while True:
        frame = shared_frame.get()
        if frame is None:
            time.sleep(0.05)
            continue

        # qr_results = qr_reader.scan(frame)
        # if len(qr_results) > 0:
        #     from utils.buffer import tx_queue
        #     tx_queue.put("S\n")      # AGV 정지
        #     time.sleep(0.6)          # 0.8초 멈춤 (값은 실험적으로!)

        qr_results = qr_reader.scan(frame)
        for qr in qr_results:
            if qr["id"]:
                agv_messenger.send_qr_info(qr["id"])
        time.sleep(0.01)

if __name__=='__main__':
    from picamera2 import Picamera2

    picam2 = Picamera2()
    picam2.configure(
    picam2.create_video_configuration(
        main={"format": "RGB888", "size": (640, 480)},
        controls={"FrameDurationLimits": (10000, 10000)}  # 100fps 시도
        )
    )




    picam2.start()

    shared_frame = SharedFrame()
    qr_reader = QRReader(cooldown=1)

    # 메인 스레드는 종료되지 않게 대기
    try:
        while True:
            frame = picam2.capture_array()

            qr_id = qr_reader.scan(frame)
            print(qr_id)

            cv2.imshow("QR Code", frame)

            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break

            time.sleep(1)
    except KeyboardInterrupt:
        print("종료합니다.")
