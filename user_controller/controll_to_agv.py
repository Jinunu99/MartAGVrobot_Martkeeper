'''
컨트롤러) - 클라이언트

AGV와 컨트롤러를 연결하는 부분
'''

import socket
import threading
import json
import time

class ControllToAgv:
    def __init__(self, agv_ip, agv_port):
        self.agv_ip = agv_ip
        self.agv_port = agv_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 송신할 변수
        self.snack_cart = None  # 장바구니 리스트
        self.move_flag = None   # 다음 버튼이나 계산 버튼을 누르면 이동하라는 flag 

        # 수신할 변수
        self.agv_name = ""
        self.position_x = 0
        self.position_y = 0
        self.target_x = 0
        self.target_y = 0

        self.same_position_callback = None # 현재 위치와 목표위치가 같으면 콜백하는 함수

        # 스레드 변수
        self.send_thread = None
        self.recv_thread = None
        self.stop_event = threading.Event()  # 종료 시그널

    # 현재위치와 목표위치가 같으면 콜백하는 함수
    def set_same_position_callback(self, callback_func):
        self.same_position_callback = callback_func

    # GUI에서 쇼핑 시작 버튼을 누르면 장바구니 리스트가 여기에 저장됨
    def set_snack_cart(self, snack_list):
        self.snack_cart = snack_list
    
    # GUI에서 다음 버튼 or 계산 버튼을 누르면 Flag가 True로 바뀜
    def set_move_flag(self):
        print("바뀜바뀜")
        self.move_flag = True

    def connect(self):
        self.client_socket.connect((self.agv_ip, self.agv_port))
        print(f"AGV와 연결 완료 - {self.agv_ip}:{self.agv_port}")

        self.send_thread = threading.Thread(target=self.send_to_agv, daemon=True)
        self.recv_thread = threading.Thread(target=self.recv_from_agv, daemon=True)

        self.send_thread.start()
        self.recv_thread.start()

    # 송신할 프레임
    def send_frame(self):
        return {
            "snack_cart": self.snack_cart,
            "move_flag": self.move_flag
        }

    # (컨트롤러 -> agv)
    def send_to_agv(self):
        while not self.stop_event.is_set():
            try:
                payload = json.dumps(self.send_frame())
                self.client_socket.sendall(payload.encode())
                print(f"송신 데이터: {payload}")
                
                if self.move_flag == True:
                    self.move_flag = False

            except Exception as e:
                print(f"[송신 오류] {e}")
                break

            time.sleep(5)

    # (컨트롤러 <- agv)
    def recv_from_agv(self):
        while not self.stop_event.is_set():
            try:
                recv_data = self.client_socket.recv(1024)
                if not recv_data:
                    break
                decoded = recv_data.decode()
                print(f"수신 데이터: {decoded}")

                data = json.loads(decoded)

                if all(k in data for k in ['x', 'y', 'target_x', 'target_y']):
                    self.position_x = data['x']
                    self.position_y = data['y']
                    self.target_x = data['target_x']
                    self.target_y = data['target_y']

                if self.same_position_callback is not None:
                    if self.position_x == self.target_x and self.position_y == self.target_y:
                        print("같음")
                        self.same_position_callback(self.position_x, self.position_y)


            except Exception as e:
                print(f"[수신 오류] {e}")
                break

    def close(self):
        print("[System] 스레드 종료 시도 중...")
        self.stop_event.set()
        self.send_thread.join()
        self.recv_thread.join()
        try:
            self.client_socket.sendall("disconnect".encode())
        except:
            pass
        self.client_socket.close()
        print("AGV와 연결해제 완료")


if __name__ == "__main__":
    controll_to_agv = ControllToAgv('192.168.137.55', 9001)

    try:
        controll_to_agv.connect()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[System] Ctrl+C 감지됨 - 종료 중...")
    finally:
        controll_to_agv.close()
