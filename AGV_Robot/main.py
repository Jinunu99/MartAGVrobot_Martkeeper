
import threading
import time
import cv2
from picamera2 import Picamera2

from utils.buffer import tx_queue, rx_queue
from communication import UARTHandler
from line_tracer import LineTracer
from qr import QRReader

def start_uart(): # 쓰레드(송수신) 초기화 
    uart = UARTHandler(port='/dev/serial0', baudrate=19200)
    tx_t = threading.Thread(target=uart.uart_tx, daemon=True)
    rx_t = threading.Thread(target=uart.uart_rx, daemon=True)
    tx_t.start()
    rx_t.start()
    print("[MAIN] UART threads started")

if __name__ == "__main__":
    # 1) UART 송수신 스레드 구동
    start_uart()

    # 2) 카메라 구동
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)}))
    picam2.start()
   # 라인트레이싱 ,qr
    tracer = LineTracer()
    qr_reader = QRReader()

    try:
        while True:
            frame = picam2.capture_array() # 프레임캡쳐
            # 라인트레이서로부터 주행방향, 어노테이트이미지, 이진화이미지 받기
            direction, annotated, binary = tracer.get_direction(frame)
            #qr받기
            qr_ids = qr_reader.scan(frame)

            #  여기서 같은 프로세스의 tx_queue에 넣으면
            #  UARTHandler.uart_tx() 스레드가 바로 가져가서 전송
            tx_queue.put(direction + "\n")

            print(f"[MAIN] Direction={direction}, QR={qr_ids}")
            cv2.imshow("Annotated", annotated)
            cv2.imshow("Binary", binary)
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        picam2.stop()
        #tx_queue.put("S\n")
        cv2.destroyAllWindows()
