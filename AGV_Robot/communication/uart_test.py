# communication/uart.py
import serial
import time
import sys
from utils.buffer import rx_queue, tx_queue

class UARTHandler:
    def __init__(self, port='/dev/serial0', baudrate=19200, timeout=1):
        print("[UART] __init__: starting", flush=True)
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            print(f"[UART] __init__: opened serial on {self.ser.port}", flush=True)
        except Exception as e:
            print(f"[UART] __init__: FAILED to open serial: {e}", flush=True)
            sys.exit(1)

        tx_queue.put("Raspi Start!\r\n")
        print("[UART] __init__: pushed welcome message", flush=True)

    def uart_tx(self):
        print("[UART-TX] thread ENTERED", flush=True)
        while True:
            # 조금만 sleep 넣어서 CPU 과점유 방지
            time.sleep(0.01)
            if not tx_queue.empty():
                msg = tx_queue.get()
                print(f"[UART-TX] got from queue: {msg!r}", flush=True)
                try:
                    self.ser.write(msg.encode('ascii'))
                    self.ser.flush()
                    print(f"[UART-TX] Sent: {msg.strip()}", flush=True)
                except Exception as e:
                    print(f"[UART-TX] WRITE ERROR: {e}", flush=True)

    def uart_rx(self):
        print("[UART-RX] thread ENTERED", flush=True)
        while True:
            try:
                line = self.ser.readline()
            except Exception as e:
                print(f"[UART-RX] READ ERROR: {e}", flush=True)
                break

            if line:
                decoded = line.decode('ascii', errors='ignore').strip()
                print(f"[UART-RX] Recv raw={line!r} -> dec={decoded!r}", flush=True)
                rx_queue.put(decoded)

    def uart_close(self):
        print("[UART] Closing serial", flush=True)
        self.ser.close()

if __name__ == "__main__":
    import threading

    print("[UART] __main__: starting handler", flush=True)
    uart = UARTHandler()

    tx_thread = threading.Thread(target=uart.uart_tx, daemon=True)
    rx_thread = threading.Thread(target=uart.uart_rx, daemon=True)

    print("[UART] __main__: starting threads", flush=True)
    tx_thread.start()
    rx_thread.start()
    print("[UART] __main__: threads started", flush=True)

    try:
        while True:
            if not rx_queue.empty():
                data = rx_queue.get()
                print(f"[UART] main loop got from rx_queue: {data!r}", flush=True)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("[UART] KeyboardInterrupt, exiting…", flush=True)
        uart.uart_close()
