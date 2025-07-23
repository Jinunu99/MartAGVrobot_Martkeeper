'''테스트 코드'''
# import sys
# from PyQt5.QtWidgets import QApplication
# from communication import RecvFromAgv
# from gui import ManagerGUI, DbConnect

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     db_manager = DbConnect(
#         host='localhost',
#         user='desktop-i399nj1',
#         password='1234',      # 비밀번호 입력
#         db='manager_db',
#         charset='utf8'
#     )

# # AGV 위치 이동 (예: managerAGV를 [0, 6]로 이동)
# window.set_agv_position("userAGV1", [0, 6])
# print("userAGV1을 (0, 6)로 이동시키고 DB에도 반영했습니다.")

# # 예시: managerAGV가 [0, 3] 위치(두 번째 스낵)에 있다고 가정하고 재고 12로 수정
# window.manager_agv_x, window.manager_agv_y = [0, 1]
# window.set_snack_stock(12)
# print("managerAGV가 [0, 1]에 있을 때, 두 번째 과자 재고를 12로 업데이트했습니다.")

#     window = ManagerGUI(db_manager)
#     window.show()
#     sys.exit(app.exec_())



import sys
from PyQt5.QtWidgets import QApplication
from communication import RecvFromAgv
from gui import ManagerGUI, DbConnect
import threading


app = QApplication(sys.argv)
db_manager = DbConnect(
    host='localhost',
    user='desktop-i399nj1', # tailscale 아이디
    password='1234',        # 비밀번호 입력
    db='manager_db',
    charset='utf8'
)

# GUI 객체를 생성할 땐 DB와 연결
window = ManagerGUI(db_manager)
window.show()

# 수신받은 정보를 GUI 객체에 전달하기 위해 이렇게 객체 생성
recv_from_agv = RecvFromAgv(window)

# 수신스레드 시작
mqtt_recv_thread = threading.Thread(target=recv_from_agv.start, daemon=True).start()

sys.exit(app.exec_())
