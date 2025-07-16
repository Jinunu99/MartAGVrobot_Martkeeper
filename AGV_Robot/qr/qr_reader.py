# from picamera2 import Picamera2
# import cv2
# from pyzbar.pyzbar import decode
# import requests
# import time

# class QRReaderSender:
#     """
#     Picamera2 기반 QR 인식 및 서버 전송 기능을 클래스화한 모듈입니다.
#     """
#     def __init__(self, server_url, delay_seconds=2, resolution=(320, 240)):
#         self.server_url = server_url
#         self.delay_seconds = delay_seconds
#         self.resolution = resolution
#         self.last_sent_id = None
#         self.last_sent_time = 0

#         # Picamera2 초기화 및 설정
#         self.picam2 = Picamera2()
#         preview_config = self.picam2.create_preview_configuration(
#             main={"format": "RGB888", "size": self.resolution}
#         )
#         self.picam2.configure(preview_config)
#         self.picam2.start()

#     def start(self):
#         """
#         QR 인식 루프를 시작합니다. 'q' 키로 종료.
#         """
#         print("[INFO] QR 인식 시작. 'q' 키로 종료")
#         try:
#             while True:
#                 frame = self.picam2.capture_array()  # NumPy array (RGB888)
#                 if frame is None:
#                     continue

#                 decoded_objs = decode(frame)
#                 now = time.time()

#                 for obj in decoded_objs:
#                     qr_data = obj.data.decode('utf-8')

#                     # 중복 전송 방지
#                     if qr_data == self.last_sent_id and now - self.last_sent_time < self.delay_seconds:
#                         continue

#                     print(f"[INFO] 인식된 QR: {qr_data}")
#                     self._send_to_server(qr_data)

#                     # 기록 업데이트
#                     self.last_sent_id = qr_data
#                     self.last_sent_time = now

#                     # 시각화
#                     x, y, w, h = obj.rect
#                     cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
#                     cv2.putText(
#                         frame, qr_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
#                         0.7, (0, 255, 0), 2
#                     )

#                 # RGB→BGR 변환 후 윈도우 표시
#                 bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
#                 cv2.imshow("QR Scanner", bgr_frame)
#                 if cv2.waitKey(1) & 0xFF == ord('q'):
#                     break
#         finally:
#             self.picam2.stop()
#             cv2.destroyAllWindows()

#     def _send_to_server(self, qr_data):
#         """
#         QR 데이터를 서버로 전송합니다.
#         """
#         try:
#             resp = requests.post(self.server_url, json={"qr_id": qr_data}, timeout=2)
#             if resp.status_code == 200:
#                 print("[✅] 서버에 전송 완료")
#             else:
#                 print(f"[⚠️] 서버 응답 오류: {resp.status_code}")
#         except Exception as e:
#             print(f"[❌] 서버 전송 실패: {e}")


# 아래 메인코드로 실행
# from qr_reader import QRReaderSender

# def main():
#     server_url = "http://your-server-ip-or-domain/api/qr"
#     reader = QRReaderSender(server_url, delay_seconds=2, resolution=(320, 240))
#     reader.start()

# if __name__ == "__main__":
#     main()

from pyzbar.pyzbar import decode
import cv2
import time

class QRReader:
    def __init__(self, cooldown=2):
        self.last_id = None
        self.last_time = 0
        self.cooldown = cooldown

    def scan(self, frame):
        result = []
        decoded = decode(frame)
        now = time.time()
        for obj in decoded:
            qr_id = obj.data.decode()
            if qr_id == self.last_id and now - self.last_time < self.cooldown:
                continue
            self.last_id = qr_id
            self.last_time = now

            x, y, w, h = obj.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, qr_id, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)
            result.append(qr_id)
        return result