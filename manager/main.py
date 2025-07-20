# import sys
# from PyQt5.QtWidgets import QApplication
# from manager_gui import ManagerGUI
# from db_connect import DbConnect

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     db_manager = DbConnect(
#         host='localhost',
#         user='desktop-i399nj1',
#         password='1234',      # 비밀번호 입력
#         db='manager_db',
#         charset='utf8'
#     )

#     db_manager.update_agv_position("managerAGV", 5, 5)
#     print("managerAGV 위치를 (5,5)로 변경했습니다.")

#     # 2. 과자 재고 변경 테스트 (qr_info=3번(후레쉬베리)의 재고를 99로 변경)
#     db_manager.update_snack_stock(3, 99)
#     print("qr_info=3번(후레쉬베리)의 재고를 99로 변경했습니다.")

#     window = ManagerGUI(db_manager)
#     window.show()
#     sys.exit(app.exec_())


# main.py
import sys
from PyQt5.QtWidgets import QApplication
from manager_gui import ManagerGUI
from db_connect import DbConnect

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db_manager = DbConnect(
        host='localhost',
        user='desktop-i399nj1',
        password='1234',      # 비밀번호 입력
        db='manager_db',
        charset='utf8'
    )

    window = ManagerGUI(db_manager)
    window.show()

    # --- 여기서 바로 테스트용 함수 호출 ---
    # AGV 위치 이동 (예: managerAGV를 [5, 5]로 이동)
    window.set_agv_position("userAGV1", [5, 5])
    print("userAGV1을 (5, 5)로 이동시키고 DB에도 반영했습니다.")

    # 예시: managerAGV가 [0, 3] 위치(두 번째 스낵)에 있다고 가정하고 재고 12로 수정
    window.manager_agv_x, window.manager_agv_y = [0, 1]
    window.set_snack_stock(12)
    print("managerAGV가 [0, 1]에 있을 때, 두 번째 과자 재고를 12로 업데이트했습니다.")

    sys.exit(app.exec_())
