# import paho.mqtt.client as mqtt
# import json
# import time
# import random

# class AgvToServer:
#     def __init__(self, agv_name):
#         self.BROKER_IP = "192.168.137.235"   # 관제센터 IP
#         self.BROKER_PORT = 1883
#         self.agv_name = agv_name
#         self.TOPIC = f"agv/{self.agv_name}/position"
#         self.client = mqtt.Client(client_id=f"{self.agv_name}")
#         self.client.connect(self.BROKER_IP, self.BROKER_PORT)
        
#         self.position_x = 0                 # AGV x 위치
#         self.position_y = 0                 # AGV y 위치

#     def set_position(self, x, y): # AGV의 위치정보가 바뀌면 set_position을 통해 업데이트 해줘야 함
#         self.position_x = x
#         self.position_y = y

#     def get_position(self):
#         return {"name": self.agv_name, "x": self.position_x, "y": self.position_y}

#     def transmit_to_server(self):
#         pos = self.get_position()
#         payload = json.dumps(pos)
#         self.client.publish(self.TOPIC, payload) # 
#         print(f"[{self.agv_name}] 위치 전송 완료: {payload}")



# if __name__ == "__main__":
#     agv_to_server = AgvToServer("userAGV2")   # userAGV1, userAGV2, managerAGV 중 AGV에 맞는 이름으로 넣기

#     while True:
#         agv_to_server.set_position(random.randint(0, 500), random.randint(0, 500))
#         agv_to_server.transmit_to_server()
#         time.sleep(2)  # 2초 간격 전송


import paho.mqtt.client as mqtt
import json
import time
import random

class AgvToServer:
    def __init__(self, agv_name):
        self.SEND_TOPIC = f"agv/{agv_name}/qr_id"  # QR 정보 송신 토픽
        self.RECV_TOPIC = f"agv/{agv_name}/pos"    # 위치 정보 수신 토픽

        self.BROKER_IP = "192.168.137.235"   # 관제센터 IP

        self.BROKER_PORT = 1883
        self.agv_name = agv_name

        self.client = mqtt.Client(client_id=f"{agv_name}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.BROKER_IP, self.BROKER_PORT)

        self.agv_qr = ""       # AGV QR 정보
        self.position_x = 0    # AGV x 위치
        self.position_y = 0    # AGV y 위치

    def get_position(self):
        return {"x": self.position_x, "y": self.position_y}

    def on_connect(self, client, userdata, flags, rc):
        print(f"[{self.agv_name}] MQTT 연결 성공" if rc == 0 else f"MQTT 연결 실패: {rc}")
        client.subscribe(self.RECV_TOPIC)
        print(f"[{self.agv_name}] {self.RECV_TOPIC} 구독 시작")

    # QR에 맞는 위치 정보를 수신함
    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())
        self.position_x = data["x"]
        self.position_y = data["y"]
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
    agv = AgvToServer("userAGV2")
    agv.start()
    time.sleep(1)
    try:
        while True:
            qr_id = f"QR:{random.randint(1, 100):03}"
            agv.send_qr_info(qr_id)
            time.sleep(5)  # 5초마다 QR 송신
    except KeyboardInterrupt:
        print("종료")
    finally:
        agv.stop()


