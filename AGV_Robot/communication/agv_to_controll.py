'''
AGV) - 서버

사용자 AGV가 컨트롤러와 송수신
사용자 AGV가 2개이기 때문에 원하는 AGV로 연결해서 통신
'''

import socket
import threading
import json
import time
import random

class AgvToControll:
    def __init__(self, agv_name):
        self.host = '0.0.0.0' # 모든 네트워크 접근 허용
        self.port = 9001      # 서버가 열릴 포트 번호
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None

        # 송신할 변수
        self.agv_name = agv_name  # AGV 이름
        self.position_x = 0       # AGV x 위치
        self.position_y = 0       # AGV y 위치
        self.target_x = 0         # AGV 다음 x 위치
        self.target_y = 0         # AGV 다음 y 위치

        # 수신할 변수


        # 스레드 관련 변수
        self.running = False
        self.send_thread = None
        self.recv_thread = None
        self.test_thread = None

        # 이벤트 처리 변수
        self.send_event = threading.Event()

    # AGV의 위치정보가 바뀌거나 목표 위치정보가 바뀌면
    # 무조건 컨트롤러에 송신하도록
    def set_position(self, x, y, t_x, t_y):
        self.position_x = x
        self.position_y = y

        self.target_x = t_x
        self.target_y = t_y

        self.send_event.set() # 송신 이벤트 활성화

    # AGV <--> 컨트롤러 사이의 연결을 시작함
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"[{self.agv_name}] Listening on {self.host}:{self.port}...")
        while True:
            conn, addr = self.server_socket.accept()
            print(f"[{self.agv_name}] Connected by {addr}")

            # 연결 수립 전에 반드시 이전 연결, 스레드 모두 종료
            if self.conn:
                print(f"[{self.agv_name}] 이전 연결 종료 시도")
                self.running = False
                self.send_event.set()
                # join 전에 None check & is_alive 체크
                if self.send_thread and self.send_thread.is_alive():
                    self.send_thread.join()
                if self.recv_thread and self.recv_thread.is_alive():
                    self.recv_thread.join()
                if self.test_thread and self.test_thread.is_alive():
                    self.test_thread.join()
                try:
                    self.conn.close()
                except Exception:
                    pass
                self.conn = None

            self.conn = conn
            self.running = True

            # 송신 스레드
            self.send_thread = threading.Thread(target=self.send_to_controller)
            # 수신 스레드
            self.recv_thread = threading.Thread(target=self.recv_from_controller, args=(addr,))
            # # 테스트 스레드
            # self.test_thread = threading.Thread(target=self.test_test_test)

            self.send_thread.start()
            self.recv_thread.start()
            #self.test_thread.start()

    def send_frame(self):
        return {
            "name": self.agv_name,
            "x": self.position_x, "y": self.position_y,
            "target_x": self.target_x, "target_y": self.target_y
        }

    # (AGV -> 컨트롤러): 컨트롤러에 데이터를 송신함
    def send_to_controller(self):
        while self.running:
            self.send_event.wait() # 이벤트가 발생될때까지 대기
            self.send_event.clear() # 이벤트 다시 비활성화

            if not self.running:
                break
            if self.conn:
                try:
                    payload = json.dumps(self.send_frame())
                    self.conn.sendall(payload.encode())
                except Exception as e:
                    print(f"송신 에러: {e}")
                    break
        print("송신스레드 종료")

    # (AGV <- 컨트롤러): 컨트롤러가 보낸 데이터를 수신함
    def recv_from_controller(self, addr):
        try:
            while self.running:
                recv_data = self.conn.recv(1024)
                if not recv_data:
                    print("데이터가 없습니다.")
                    break
                recv_data = recv_data.decode()
                print(f"수신 데이터: {recv_data}")
                
                if recv_data == "disconnect": # 연결 해제
                    break
                #else:

        finally:
            self.running = False
            self.send_event.set()
            try:
                if self.conn:
                    self.conn.close()
            except Exception:
                pass
            self.conn = None
            print(f"[{self.agv_name}] Connection closed")

    def test_test_test(self):
        flag = True
        while self.running:
            if self.conn:
                if flag:
                    self.set_position(random.randint(0, 1), random.randint(0, 1))
                    flag = False
                else:
                    self.set_target_position(random.randint(0, 1), random.randint(0, 1))
                    flag = True
            time.sleep(5)

    def close(self):
        self.running = False
        self.send_event.set()
        time.sleep(0.1)

        self.send_thread.join()
        self.recv_thread.join()
        self.test_thread.join()
        
        self.server_socket.close()
        print(f"[{self.agv_name}] 서버 종료")

if __name__ == "__main__":
    agv_to_controll = AgvToControll("userAGV2")
    
    try:
        agv_to_controll.start()
    except KeyboardInterrupt:
        print("서버 종료")
    finally:
        agv_to_controll.close()
