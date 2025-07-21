'''
관제센터)
userAGV1, userAGV2, managerAGV로부터 위치데이터를 받아오는 코드
'''
import paho.mqtt.client as mqtt
import json

class RecvFromAgv:
    def __init__(self):

        self.SEND_TOPIC = "agv/{}/pos"  # 송신할 토픽 (x, y 위치정보 송신)
        self.RECV_TOPIC = "agv/+/qr_id" # 수신할 토픽 (QR 정보 수신)

        self.BROKER_IP = "localhost"
        self.BROKER_PORT = 1883
        self.client = mqtt.Client(client_id="ControlCenter")
        self.client.connect(self.BROKER_IP, self.BROKER_PORT)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.agv_name = ["userAGV1", "userAGV2", "managerAGV"]   # userAGV1, userAGV2, managerAGV
        self.agv_qr = [None, None, None]       # AGV가 인식한 QR 정보
        self.agv_idx = None        
        self.position_x = [0, 1, None]   # AGV x 위치
        self.position_y = [0, 1, None]   # AGV y 위치


    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT 연결")
            client.subscribe(self.RECV_TOPIC)
        else:
            print("MQTT 연결 실패: ", rc)


    # 데이터가 수신될 때마다 호출되는 함수
    # AGV가 QR 정보를 송신하면 관제센터는 그에 맞는 위치정보를 송신해줘야함
    def on_message(self, client, userdata, msg):
        '''QR 정보 수신'''
        data = json.loads(msg.payload.decode())
        
        target_agv_name = msg.topic.split('/')[1]  # 송신한 AGV의 이름
        print(f"수신 데이터: [{target_agv_name}]{data}")
        
        if target_agv_name in self.agv_name:
            self.agv_idx = self.agv_name.index(target_agv_name) # 어떤 AGV가 보냈는지 저장
            self.agv_qr[self.agv_idx] = data.get("QR_info")     # QR 정보를 저장

            '''그에 맞는 위치정보 송신'''
            send_topic = self.SEND_TOPIC.format(target_agv_name)
            send_data = {"x": self.position_x[self.agv_idx], "y": self.position_y[self.agv_idx]}
            self.client.publish(send_topic, json.dumps(send_data))
            print(f"송신 데이터: {send_data}")


    def get_position(self, target_agv_name):
        if target_agv_name in self.agv_name:
            idx = self.agv_name.index(target_agv_name)
        return {"x": self.position_x[idx], "y": self.position_y[idx]}
    
    def start(self):
        self.client.loop_forever()


if __name__ == "__main__":
    recv_from_agv = RecvFromAgv()

    recv_from_agv.start()
