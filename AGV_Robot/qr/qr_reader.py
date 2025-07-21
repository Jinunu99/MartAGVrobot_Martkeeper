
from pyzbar.pyzbar import decode
import cv2
import time
import re  # 좌표 추출을 위한 정규식 사용
import json
import paho.mqtt.client as mqtt


class QRReader:
    def __init__(self, cooldown=2):
        self.last_id = None
        self.last_time = 0
        self.cooldown = cooldown

    def scan(self, frame):
        result = []
        decoded = decode(frame)  # 프레임에서 QR 코드 디코딩
        now = time.time()

        for obj in decoded:
            qr_results = obj.data.decode() # QR에서 추출한 문자열 (예: "ID:001,X:2,Y:4")

             # 중복 전송 방지 (cooldown 시간 내 동일 ID 무시)
            if qr_results == self.last_id and now - self.last_time < self.cooldown:
                continue
            self.last_id = qr_results
            self.last_time = now

            # 기본 리턴 딕셔너리 구성
            parsed_qr = {
                "raw": qr_results,  # 원본 문자열도 항상 포함
                "x": None,
                "y": None,
                "id": None
            }

            # 좌표 포함된 QR 형식이면 파싱 시도
            try:
                match = re.search(r"ID:(\d+),X:(\d+),Y:(\d+)", qr_results)
                if match:
                    parsed_qr["id"] = f"ID:{match.group(1)}"
                    parsed_qr["x"] = int(match.group(2))
                    parsed_qr["y"] = int(match.group(3))
            except Exception as e:
                print(f"[QRReader] 좌표 파싱 실패: {e}")

            # 시각화: QR 인식된 위치에 사각형 + 텍스트 표시
            x, y, w, h = obj.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, qr_results, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)

            result.append(parsed_qr)  # 좌표까지 포함한 dict 형태로 결과 추가

        return result  # 리스트 형태로 여러 QR 인식 결과 반환

# from pyzbar.pyzbar import decode
# import cv2
# import time
# import mysql.connector
# import re

# class QRReader:
#     def __init__(self, cooldown=2):
#         self.last_id = None
#         self.last_time = 0
#         self.cooldown = cooldown

#         # MariaDB 연결 설정
#         self.db_config = {
#             'user': 'root',
#             'password': '',  # 비밀번호가 있으면 입력
#             'host': 'localhost',
#             'database': 'qr_reader'
#         }

#     def scan(self, frame):
#         result = []
#         decoded = decode(frame)
#         now = time.time()

#         for obj in decoded:
#             qr_id = obj.data.decode().strip()

#             # 중복 전송 방지
#             if qr_id == self.last_id and now - self.last_time < self.cooldown:
#                 continue

#             self.last_id = qr_id
#             self.last_time = now

#             parsed = {
#                 "raw": qr_id,
#                 "id": None,
#                 "x": None,
#                 "y": None
#             }

#             if qr_id.startswith("ID:"):
#                 parsed["id"] = qr_id

#                 # DB에서 매핑된 좌표 조회
#                 coord = self.lookup_coordinates(qr_id)
#                 if coord:
#                     parsed["x"] = coord["x"]
#                     parsed["y"] = coord["y"]
#                     print(f"[QRReader] 매핑 성공: {qr_id} → {coord}")
#                 else:
#                     print(f"[QRReader] DB에 {qr_id} 없음")

#             else:
#                 print(f"[QRReader] 알 수 없는 QR 형식 무시됨: {qr_id}")

#             # 디버깅용 사각형 표시
#             x, y, w, h = obj.rect
#             cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
#             cv2.putText(frame, qr_id, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
#                         0.7, (0, 255, 0), 2)

#             result.append(parsed)

#         return result

#     def lookup_coordinates(self, qr_id):
#         try:
#             conn = mysql.connector.connect(**self.db_config)
#             cursor = conn.cursor(dictionary=True)

#             cursor.execute("SELECT x, y FROM qr_table WHERE id = %s", (qr_id,))
#             result = cursor.fetchone()

#             cursor.close()
#             conn.close()

#             return result  # 예: {'x': 1, 'y': 0}
#         except mysql.connector.Error as err:
#             print(f"[DB ERROR] {err}")
#             return None
