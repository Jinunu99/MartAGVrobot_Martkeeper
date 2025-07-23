import paho.mqtt.client as mqtt
import json
import time
import random

class AgvToServer:
    def __init__(self, agv_name):
        self.SEND_TOPIC = f"agv/{agv_name}/qr_id"  # QR 정보 송신 토픽
        self.RECV_TOPIC = f"agv/{agv_name}/pos"    # 위치 정보 수신 토픽

        self.BROKER_IP = "100.92.188.21"   # 관제센터 IP

        self.BROKER_PORT = 1883
        self.agv_name = agv_name

        self.client = mqtt.Client(client_id=f"{agv_name}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.BROKER_IP, self.BROKER_PORT)

        self.agv_qr = ""       # AGV QR 정보
        self.position_x = 0    # AGV x 위치
        self.position_y = 0    # AGV y 위치

    #=======위치 수신 플래그 ======#
        self.received_pos = False  # 위치 수신 완료 여부


    def get_position(self):
        return {"x": self.position_x, "y": self.position_y}

    def on_connect(self, client, userdata, flags, rc):
        print(f"[{self.agv_name}] MQTT 연결 성공" if rc == 0 else f"MQTT 연결 실패: {rc}")
        client.subscribe(self.RECV_TOPIC)
        print(f"[{self.agv_name}] {self.RECV_TOPIC} 구독 시작")

    # QR에 맞는 위치 정보를 수신함
    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())
        self.position_x = int(data["x"])
        self.position_y = int(data["y"])
        self.received_pos = True  # 위치 수신됨
        print(f"[{self.agv_name}] 위치 정보 수신: x={self.position_x}, y={self.position_y}")

    # QR 정보를 관제센터로 송신
    def send_qr_info(self, qr_info):
        payload = json.dumps({"QR_info": qr_info})
        self.client.publish(self.SEND_TOPIC, payload)
        print(f"[{self.agv_name}] QR 정보 송신: {qr_info}")

    def start(self):
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
            

if __name__ == "__main__":
    pass
    # agv = AgvToServer("userAGV2")
    # agv.start()
    # time.sleep(1)
    # try:
    #     while True:
    #         qr_id = f"QR:{random.randint(1, 100):03}"
    #         agv.send_qr_info(qr_id)
    #         time.sleep(5)  # 5초마다 QR 송신
    # except KeyboardInterrupt:
    #     print("종료")
    # finally:
    #     agv.stop()