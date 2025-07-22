
from pyzbar.pyzbar import decode
import cv2
import time
import re  # 좌표 추출을 위한 정규식 사용
import json
from utils.buffer import tx_queue  # UART 전송 큐 사용
import paho.mqtt.client as mqtt


class QRReader:
    def __init__(self, cooldown=3.5):
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

            # 정지 명령 + 대기
            # print(f"[QRReader] QR 인식됨: {qr_results} → 정지 후 2초 대기")
            # tx_queue.put("S\n")
            # time.sleep(1.5)

            # 기본 리턴 딕셔너리 구성
            parsed_qr = {
                "raw": qr_results,  # 원본 문자열도 항상 포함
                "id": None
            }

            # 좌표 포함된 QR 형식이면 파싱 시도
            try:
                match = re.search(r"ID:(\d+)", qr_results)
                if match:
                    parsed_qr["id"] = f"ID:{match.group(1)}"
                # else:
                #     # 좌표 없는 QR도 id 추출
                #     simple_match = re.search(r"ID:(\d+)", qr_results)
                #     if simple_match:
                #         parsed_qr["id"] = f"ID:{simple_match.group(1)}"
            except Exception as e:
                print(f"[QRReader] 좌표 파싱 실패: {e}")

            # 시각화: QR 인식된 위치에 사각형 + 텍스트 표시
            x, y, w, h = obj.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, qr_results, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)

            result.append(parsed_qr)  # 좌표까지 포함한 dict 형태로 결과 추가

        return result  # 리스트 형태로 여러 QR 인식 결과 반환

