import sys
from PyQt5 import QtWidgets, uic

from controll_to_agv import ControllToAgv

class UserShoppingGui(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("user_gui.ui", self)

        self.snack_position = { "뽀또": [0, 1], "초코칩쿠키": [0, 3], "쵸코하임": [0, 5],
                            "후레쉬베리": [4, 1], "고소미": [4, 3], "빅파이": [4, 5] }

        self.snack_cart = [] # 장바구니 리스트

        self.agv_ip = ""
        self.agv_port = 9001
        self.controll_to_agv = None # 컨트롤러와 AGV 통신할 객체


        # 과자 선택 버튼
        self.btn_select1.clicked.connect(lambda: self.add_to_cart("뽀또"))
        self.btn_select2.clicked.connect(lambda: self.add_to_cart("초코칩쿠키"))
        self.btn_select3.clicked.connect(lambda: self.add_to_cart("쵸코하임"))
        self.btn_select4.clicked.connect(lambda: self.add_to_cart("후레쉬베리"))
        self.btn_select5.clicked.connect(lambda: self.add_to_cart("고소미"))
        self.btn_select6.clicked.connect(lambda: self.add_to_cart("빅파이"))

        self.listWidget_cart.itemClicked.connect(self.remove_from_cart)

        # AGV 연결 및 해제
        self.btn_connect.clicked.connect(self.connect_agv)
        self.btn_disconnect.clicked.connect(self.disconnect_agv)

        self.btn_start.clicked.connect(self.start_shopping) # 쇼핑 시작
        self.btn_next.clicked.connect(self.next_item) # 다음
        self.btn_pay.clicked.connect(self.pay)  # 계산

    # 장바구니 추가
    def add_to_cart(self, item_name):
        self.listWidget_cart.addItem(item_name)
        self.snack_cart.append(self.snack_position[item_name]) # 과자 위치를 추가
        print(self.snack_cart)
    
    # 장바구니 삭제
    def remove_from_cart(self, item):
        item_name = item.text()                   # 삭제할 과자 이름
        row = self.listWidget_cart.row(item)
        self.listWidget_cart.takeItem(row)

        item_pos = self.snack_position[item_name] # 삭제할 과자 위치
        self.snack_cart.remove(item_pos)
        print(self.snack_cart)

    # 쇼핑 시작버튼을 누르게 되면 장바구니에 있는 품목의 위치들이 전송되기 시작함
    def start_shopping(self):
        self.controll_to_agv.set_snack_cart(self.snack_cart)
        self.textEdit_log.append("쇼핑을 시작합니다.")

    # 현재위치와 목표위치가 같을때
    def now_next_position_same(self, x, y):
        self.textEdit_log.append(f"AGV가 목표 위치({x}, {y})에 도착했습니다.")

        # snack_cart에서 해당 좌표를 삭제
        for idx, pos in enumerate(self.snack_cart):
            if pos[0] == x and pos[1] == y:
                del self.snack_cart[idx]
                break

        # 장바구니에서 해당 물품 삭제
        for i in range(self.listWidget_cart.count()):
            item = self.listWidget_cart.item(i)
            if self.snack_position[item.text()] == [x, y]:
                self.listWidget_cart.takeItem(i)
                break
        
        if self.listWidget_cart.count():
            self.textEdit_log.append("다음 항목으로 이동을 원하면 다음 버튼을 눌러주세요.")
        else:
            self.textEdit_log.append("계산대로 이동을 원하면 계산 버튼을 눌러주세요.")



    # AGV 다음
    def next_item(self):
        self.controll_to_agv.set_move_flag()
        self.textEdit_log.append("다음 항목으로 이동합니다.")

    # 계산대 이동
    def pay(self):
        self.controll_to_agv.set_move_flag()
        self.textEdit_log.append("계산대로 이동합니다.")

    

    # AGV 연결
    def connect_agv(self):
        agv_name = self.comboBox.currentText()
        
        if agv_name == "userAGV1":
            self.agv_ip = "192.168.137.55"
        elif agv_name == "userAGV2":
            self.agv_ip = "192.168.137.55" # 주소에 맞게 바꿔야 함
        
        if self.controll_to_agv is None:
            self.controll_to_agv = ControllToAgv(self.agv_ip, self.agv_port)
            self.controll_to_agv.connect()
            self.controll_to_agv.set_same_position_callback(self.now_next_position_same)
            self.textEdit_log.append(f"{agv_name} [{self.agv_ip}] 연결 완료")
        else:
            self.textEdit_log.append("이미 연결되어있습니다")

    # AGV 연결 해제
    def disconnect_agv(self):
        agv_name = self.comboBox.currentText()

        if self.controll_to_agv:
            self.controll_to_agv.close()
            self.textEdit_log.append(f"{agv_name} 연결 해제 완료")
            self.controll_to_agv = None

            # 장바구니 목록 비우기
            self.snack_cart = []
            self.listWidget_cart.clear()
        else:
            self.textEdit_log.append("연결된 AGV가 없습니다")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = UserShoppingGui()
    window.show()
    sys.exit(app.exec_())
