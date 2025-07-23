import serial
import time
from utils.buffer import rx_queue, tx_queue

class UARTHandler:
    def __init__(self, port='/dev/serial0', baudrate=19200, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        tx_queue.put("Raspi Start!\r\n")  #  큐에 넣기

    def uart_tx(self):
        while True:
            # tx_queue.get()은 큐에 데이터가 없으면 블록킹 대기함
            msg = tx_queue.get()            
            # 바로 보내고 플러시
            self.ser.write(msg.encode('ascii'))
            self.ser.flush()  # 출력 버퍼 비우기
            # 더 이상 딜레이 없음    

    def uart_rx(self):
        while True:
            line = self.ser.readline()
            if line:
                decoded = line.decode('ascii').strip()
                rx_queue.put(decoded)
    
    def uart_close(self):
        self.ser.close()
                
# sudo python -m communication.uart 명령어로 실행
# /dev/serial0의 사용 현황 : sudo lsof /dev/serial0
# sudo kill -9 1234
if __name__=="__main__":
    import threading
    
    uart = UARTHandler()
    tx_thread = threading.Thread(target=uart.uart_tx, daemon=True)
    rx_thread = threading.Thread(target=uart.uart_rx, daemon=True)
    tx_thread.start()
    rx_thread.start()
    
    try:
        print("[UART] UART handler running. Waiting for messages...")

        while True:
            # 수신된 데이터 있으면 출력만 함
            if not rx_queue.empty():
                data = rx_queue.get()
                print(f"[UART] Received from STM32: {data}")

            time.sleep(0.01)  # CPU 과점유 방지용
    
    except KeyboardInterrupt:
        print("User KeyboardInterrupt")
        uart.uart_close()
    
    except Exception as e:
        print(f"Error {e}")
        uart.uart_close()