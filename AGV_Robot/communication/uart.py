import serial
import time
from utils.buffer import rx_queue, tx_queue

class UARTHandler:
    def __init__(self, port='/dev/serial0', baudrate=19200, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        tx_queue = "Raspi Start!\r\n"
    
    def uart_tx(self):
        while True:
            if not tx_queue.empty():
                msg = tx_queue.get()
                self.ser.write(msg.encode('ascii'))
                self.ser.flush()
                time.sleep(1)
        
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
        msg = "Hello STM32\r\n"
        while True:
            tx_queue.put(msg)
            if not rx_queue.empty():
                data = rx_queue.get()
                print(f"Received from rx_queue: {data}")
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("User KeyboardInterrupt")
        uart.uart_close()
    
    except Exception as e:
        print(f"Error {e}")
        uart.uart_close()