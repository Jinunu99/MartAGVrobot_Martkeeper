import threading
import time
import cv2
import numpy as np
from picamera2 import Picamera2

from utils.buffer import tx_queue, rx_queue
from communication import UARTHandler
from line_tracer import LineTracer
from qr import QRReader

def start_uart():
    uart = UARTHandler(port='/dev/serial0', baudrate=19200)
    tx_t = threading.Thread(target=uart.uart_tx, daemon=True)
    rx_t = threading.Thread(target=uart.uart_rx, daemon=True)
    tx_t.start()
    rx_t.start()
    print("[MAIN] UART threads started")

if __name__ == "__main__":
    # 1) UART 송수신 스레드 시작
    start_uart()

    # 2) 카메라 설정
    picam2 = Picamera2()
    picam2.configure(
    picam2.create_video_configuration(
        main={"format": "RGB888", "size": (640, 480)},
        controls={"FrameDurationLimits": (10000, 10000)}  # 100fps 시도
        )
    )

    picam2.start()

    # 3) 라인트레이서, QR 리더 초기화
    tracer = LineTracer()
    qr_reader = QRReader()
    
    try:
        while True:
            frame = picam2.capture_array()

            # 라인트레이서 메서드 사용
            direction, offset, annotated, binary, found = tracer.get_direction(frame)

            # QR 코드 인식
            qr_string = qr_reader.scan(frame)

            # UART 송신
            tx_queue.put(direction + "\n")

            # line_tracer 값 출력
            print(f"[MAIN] Direction={direction}, Offset={offset}, Found={found}, QR={qr_string}")

            # 디버깅 이미지 표시
            combined = tracer.draw_debug(annotated, binary)
            cv2.imshow("LineTracer (Annotated + Binary)", combined)

            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break

    except KeyboardInterrupt:
        pass
    finally:
        tx_queue.put("S\n")
        picam2.stop()
        cv2.destroyAllWindows()

