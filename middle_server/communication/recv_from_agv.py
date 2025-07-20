'''
관제센터)
userAGV1, userAGV2, managerAGV로부터 위치데이터를 받아오는 코드
'''
import paho.mqtt.client as mqtt
import json

class RecvFromAgv:
    def __init__(self):
        self.BROKER_IP = "localhost"
        self.BROKER_PORT = 1883
        self.TOPIC = "agv/+/position"
        self.client = mqtt.Client(client_id="ControlCenter")
        self.client.connect(self.BROKER_IP, self.BROKER_PORT)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.agv_name = ["userAGV1", "userAGV2", "managerAGV"]   # userAGV1, userAGV2, managerAGV
        self.position_x = [None, None, None]   # AGV x 위치
        self.position_y = [None, None, None]   # AGV y 위치

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[Control Center] Connected to MQTT broker successfully")
            client.subscribe(self.TOPIC)
        else:
            print("[Control Center] Connection failed. Return code:", rc)

    # 데이터가 수신될 때마다 호출되는 함수
    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())
        print(f"[Control Center] Recv data: {data}")
        self.parsing(data)

        print(recv_from_agv.get_position("userAGV1")) # 이 함수를 통해 위치를 받아옴

    # 전송 받은 데이터가 어떤 AGV인지 파악해서 위치를 저장하는 함수 
    def parsing(self, data):
        target_agv_name = data.get("name")

        if target_agv_name in self.agv_name:
            idx = self.agv_name.index(target_agv_name)
            self.position_x[idx] = data.get("x")
            self.position_y[idx] = data.get("y")

    def get_position(self, target_agv_name):
        if target_agv_name in self.agv_name:
            idx = self.agv_name.index(target_agv_name)
        return {"x": self.position_x[idx], "y": self.position_y[idx]}
    
    def start(self):
        self.client.loop_forever()


if __name__ == "__main__":
    recv_from_agv = RecvFromAgv()

    recv_from_agv.start()
