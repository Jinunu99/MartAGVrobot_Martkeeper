'''
관제센터)
userAGV1, userAGV2, managerAGV로부터 위치데이터를 받아오는 코드
'''
import paho.mqtt.client as mqtt
import json
import mysql.connector

class RecvFromAgv:
    def __init__(self, manager_gui):

        self.manager_gui = manager_gui  # GUI 객체

        self.SEND_TOPIC = "agv/{}/pos"  # 송신할 토픽 (x, y 위치정보 송신)
        self.RECV_TOPIC = "agv/+/qr_id" # 수신할 토픽 (QR 정보 수신)


        self.BROKER_IP = "localhost" # 브로커 IP는 실행하는 라즈베리파이 주소 입력
        self.BROKER_PORT = 1883
        self.client = mqtt.Client(client_id="ControlCenter")
        self.client.connect(self.BROKER_IP, self.BROKER_PORT)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.agv_name = ["userAGV1", "userAGV2", "managerAGV"]   # userAGV1, userAGV2, managerAGV
        self.agv_qr = [None, None, None]       # AGV가 인식한 QR 정보
        self.agv_idx = None        

        self.position_x = [None, None, None]   # AGV x 위치
        self.position_y = [None, None, None]   # AGV y 위치

        self.position_x = [0, 1, None]   # AGV x 위치
        self.position_y = [0, 1, None]   # AGV y 위치


        self.snack_num = None
        
    #---------DB 연결 설정--------#
        self.db_config = {
            'user': 'root',         # DB 계정
            'password': '1234',         # DB 비밀번호 (있으면 입력)
            'host': '100.123.1.124',    # DB 서버
            'database': 'qr_reader'
        }
    #------------------------#

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT 연결")
            client.subscribe(self.RECV_TOPIC)
        else:
            print("MQTT 연결 실패: ", rc)

    #===========db id조회==============#
    def lookup_coordinates(self, qr_id):
        print(f"[DB QUERY] QR ID: {qr_id}")  # 쿼리 요청 로그
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT x, y FROM qr_table WHERE id = %s", (qr_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            print(f"[DB RESULT] {result}")  # DB 결과 로그
            if result:
                return result['x'], result['y']
            else:
                return None, None
        except mysql.connector.Error as err:
            print(f"[DB ERROR] {err}")
            return None, None

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
            qr_id = self.agv_qr[self.agv_idx]

            if "snack_num" in data: # 재고 갯수를 저장
                self.snack_num = data["snack_num"] # {'haetae_Osajjeu_60G': 1}

                # # GUI에 재고 갱신
                # self.manager_gui.snack_updated.emit(idx, data['snack_num'])
                # for product_name, count in detection_results.items():
                for product_name, count in snack_num.items():
                    self.manager_gui.db_manager.update_snack_stock(product_name, count)
                    print(f"DB 업데이트: {product_name} → {count}개")

            # --- MariaDB에서 해당 QR ID로 x, y 좌표를 조회 ---
            x, y = self.lookup_coordinates(qr_id)
            if x is not None and y is not None:
                self.position_x[self.agv_idx] = x
                self.position_y[self.agv_idx] = y
            else:
                print(f"[WARN] DB에 {qr_id} 없음")
                self.position_x[self.agv_idx] = -1
                self.position_y[self.agv_idx] = -1
            #--------------------------------------------------#

            # GUI에 위치 갱신
            self.manager_gui.agv_position_updated.emit(target_agv_name, x, y)


            '''그에 맞는 위치정보 송신'''
            send_topic = self.SEND_TOPIC.format(target_agv_name)
            
            send_data = {
                "x": self.position_x[self.agv_idx],
                "y": self.position_y[self.agv_idx]
            }

            
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
