import paho.mqtt.client as mqtt
import json

import time
import random

class AgvToServer:
    def __init__(self, agv_name):
        self.BROKER_IP = "192.168.137.235"   # 관제센터 IP
        self.BROKER_PORT = 1883
        self.agv_name = agv_name
        self.TOPIC = f"agv/{self.agv_name}/position"
        self.client = mqtt.Client(client_id=f"{self.agv_name}")
        self.client.connect(self.BROKER_IP, self.BROKER_PORT)
        
        self.position_x = 0                 # AGV x 위치
        self.position_y = 0                 # AGV y 위치

    def set_position(self, x, y): # AGV의 위치정보가 바뀌면 set_position을 통해 업데이트 해줘야 함
        self.position_x = x
        self.position_y = y

    def get_position(self):
        return {"name": self.agv_name, "x": self.position_x, "y": self.position_y}

    def transmit_to_server(self):
        pos = self.get_position()
        payload = json.dumps(pos)
        self.client.publish(self.TOPIC, payload) # 
        print(f"[{self.agv_name}] 위치 전송 완료: {payload}")



if __name__ == "__main__":
    agv_to_server = AgvToServer("userAGV2")   # userAGV1, userAGV2, managerAGV 중 AGV에 맞는 이름으로 넣기

    while True:
        agv_to_server.set_position(random.randint(0, 500), random.randint(0, 500))
        agv_to_server.transmit_to_server()
        time.sleep(2)  # 2초 간격 전송
