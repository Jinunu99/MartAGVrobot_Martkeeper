import time
import threading
import json
from SX127x.LoRa import LoRa
from SX127x.board_config import BOARD
from SX127x.constants import *

# LoRa 모듈 클래스 (기존과 동일)
class MeshAGV(LoRa):
    def __init__(self, agv_name, verbose=False):
        super().__init__(verbose)
        self.agv_name = agv_name
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0,0,0,0,0,0])  # DIO0=RxDone

        # LoRa 파라미터 설정
        self.set_freq(433.0)
        self.set_pa_config(pa_select=1, max_power=0x04, output_power=14)
        self.set_spreading_factor(7)
        self.set_bw(7)
        self.set_coding_rate(CODING_RATE.CR4_5)
        self.set_preamble(8)
        self.set_sync_word(0x12)

        # 수신데이터를 AgvToAgv 클래스에 반환하기 위함
        self.recv_callback = None
    
    def set_recv_callback(self, callback):
        self.recv_callback = callback

    def on_rx_done(self):
        payload = self.read_payload(nocheck=True)
        try:
            msg = ''.join([chr(c) for c in payload if 32 <= c <= 126])
            packet = json.loads(msg)
            dst = packet.get("dst", "")
            if dst == self.agv_name or dst == "all":
                print(f"[{self.agv_name}] 수신완료!: {msg}")
                print(f"[{self.agv_name}] ==> {packet['src']}로부터 x={packet['x']} y={packet['y']}")
                if self.recv_callback:
                    self.recv_callback(packet)
        except Exception as e:
            pass
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_dio_mapping([0,0,0,0,0,0])  # DIO0=RxDone
        self.set_mode(MODE.RXCONT) # 수신 대기상태로 바꿔라

    def on_tx_done(self):
        print(f"[{self.agv_name}] 송신 완료 → RX 대기 진입")
        self.set_dio_mapping([0,0,0,0,0,0])  # DIO0=RxDone
        self.set_mode(MODE.RXCONT)

class AgvToAgv:
    def __init__(self, agv_name):
        self.agv_name = agv_name
        self.lora = MeshAGV(agv_name, verbose=False)
        self.running = True

        # AGV의 모든 위치를 관리하는 변수
        self.total_agv_name = ["userAGV1", "userAGV2", "managerAGV"]
        self.total_agv_pos_x = [None, None, None]
        self.total_agv_pos_y = [None, None, None]

        # AGV별 송신 타임 슬롯 설정 (6초 주기)
        self.slot_map = {
            "userAGV1": 0,
            "userAGV2": 2,
            "managerAGV": 4
        }
        self.slot_period = 6  # 6초 주기 (0~5초)
        self.counter = 0

        self.lora.set_recv_callback(self.packet_recv) # 패킷정보를 받기 위한 콜백함수

    # 자신의 위치를 리스트에 저장하기 위함
    def set_my_position(self, x, y):
        if self.agv_name in self.total_agv_name:
            idx = self.total_agv_name.index(self.agv_name)
            self.total_agv_pos_x[idx] = x
            self.total_agv_pos_y[idx] = y
    
    # 수신받은 패킷을 해당 클래스에 적용하는 함수
    # 패킷을 수신받으면 {'src': 'userAGV1', 'dst': 'all', 'x': 268, 'y': 368}
    # 해당 형태로 수신될텐데 파싱을 해서 모든 AGV의 위치를 저장되도록 함
    def packet_recv(self, packet):
        src_agv_name = packet['src']
        x = packet['x']
        y = packet['y']

        if src_agv_name in self.total_agv_name:
            idx = self.total_agv_name.index(src_agv_name)
            self.total_agv_pos_x[idx] = x
            self.total_agv_pos_y[idx] = y

    def main_loop(self):
        prev_slot = None # 이전 슬롯 변수
        while self.running:
            now = int(time.time())
            slot = now % self.slot_period # 0 ~ 5 사이의 값이 반환

            my_slot = self.slot_map.get(self.agv_name) # 해당 AGV의 송신 슬롯의 시간을 반환
            if my_slot == slot: # 해당 AGV가 송신할 시간이 되면

                if self.agv_name == "userAGV1":
                    self.total_agv_pos_x[0], self.total_agv_pos_x[0] = 100 + self.counter, 200 + self.counter
                elif self.agv_name == "userAGV2":
                    self.total_agv_pos_x[1], self.total_agv_pos_x[1] = 300 + self.counter, 400 + self.counter
                elif self.agv_name == "managerAGV":
                    self.total_agv_pos_x[2], self.total_agv_pos_x[2] = 500 + self.counter, 600 + self.counter

                # 자신의 위치를 담아서 송신할 수 있도록
                if self.agv_name in self.total_agv_name:
                    idx = self.total_agv_name.index(self.agv_name)
                    x = self.total_agv_pos_x[idx]
                    y = self.total_agv_pos_y[idx]

                send_packet = {
                    "src": self.agv_name,
                    "dst": "all",
                    "x": x,
                    "y": y
                }
                msg = json.dumps(send_packet)
                payload = [ord(c) for c in msg]
                
                # 같은 시간 슬롯에 진입했을때 한번만 송신하도록
                if prev_slot != slot:
                    # 송신 모드로 바꿔주고 송신
                    self.lora.set_dio_mapping([1,0,0,0,0,0])  # DIO0: TxDone
                    self.lora.write_payload(payload)
                    self.lora.set_mode(MODE.TX)
                    print(f"[{self.agv_name}] SLOT {slot} 송신 → all: {msg}")
                    self.counter += 1

                    time.sleep(0.3)

                    # 송신이 끝나면 곧바로 수신모드로
                    self.lora.set_dio_mapping([0,0,0,0,0,0])  # DIO0=RxDone
                    self.lora.set_mode(MODE.RXCONT)
                    time.sleep(0.1)

            prev_slot = slot # 현재 슬롯이 이전 슬롯 변수에 할당 (해당 슬롯에서 송신을 한번만 하기 위함)


    def start(self):
        print(f"[{self.agv_name}] Mesh 네트워크 실행 시작!")
        self.running = True
        t = threading.Thread(target=self.main_loop, daemon=True)
        t.start()
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("종료 신호 감지, 프로그램 종료.")
            self.running = False
            BOARD.teardown()

if __name__ == "__main__":
    BOARD.setup()
    lora_lock = threading.Lock()
    
    agv_to_agv = AgvToAgv("userAGV2")  # "userAGV1", "userAGV2", "managerAGV"
    agv_to_agv.start()
