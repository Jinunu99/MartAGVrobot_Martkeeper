import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem
from PyQt5.QtWidgets import QGraphicsView, QLabel
from PyQt5 import uic
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt

import pymysql

class ManagerGUI(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        uic.loadUi("manager_gui.ui", self)

        self.db_manager = db_manager # DB 객체

        # agv 위치 저장 변수
        self.user_agv1_x, self.user_agv1_y = [0, 5]
        self.user_agv2_x, self.user_agv2_y = [0, 5]
        self.manager_agv_x, self.manager_agv_y = [0, 4]


        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        # 맵 그리기
        self.cell_size = 60
        self.draw_map()

        # AGV 표시를 위한 원 생성
        self.agv1 = self.draw_agv(0, 5, Qt.red)
        self.agv2 = self.draw_agv(0, 5, Qt.blue)
        self.agv_admin = self.draw_agv(0, 4, Qt.green)

        self.snack_name = ["뽀또", "초코칩", "쵸코하임", "후레쉬베리", "고소미", "빅파이"] # 과자 재고 이름
        self.snack_position = [[0, 1], [0, 3], [0, 5], [4, 1], [4, 3], [4, 5]] # 과자 재고 위치
        self.snack_num = [0, 0, 0, 0, 0, 0] # 과자 재고 갯수

        for i in range(6):
            label = getattr(self, f"lbl_snack_name{i + 1}")
            label.setText(self.snack_name[i])

        # DB에 agv 위치 초기화 
        self.set_agv_position("userAGV1", [self.user_agv1_x, self.user_agv1_y])
        self.set_agv_position("userAGV2", [self.user_agv2_x, self.user_agv2_y])
        self.set_agv_position("managerAGV", [self.manager_agv_x, self.manager_agv_y])

        # DB에 재고 갯수 초기화
        self.set_snack_db_init()

    # agv 그리기
    def draw_agv(self, x, y, color):
        agv = QGraphicsEllipseItem(x * self.cell_size, y * self.cell_size,
                                   self.cell_size, self.cell_size)
        agv.setBrush(QBrush(color))
        self.scene.addItem(agv)
        return agv

    # agv 원 이동
    def update_agv_position(self, agv_item, x, y):
        """AGV 위치 이동"""
        agv_item.setRect(x * self.cell_size, y * self.cell_size,
                         self.cell_size, self.cell_size)


    # AGV 위치 업데이트 함수
    # 실제 agv가 이동하면 해당 함수를 호출해서 agv의 현재 위치 알려주기
    # 해당 함수를 호출할때 agv_name과 업데이트된 x 위치, y위치를 알려줘야함
    # agv_name : userAGV1, userAGV2, managerAGV
    # pos는 [x, y]
    def set_agv_position(self, agv_name, agv_position):
        if agv_name == "userAGV1":
            self.user_agv1_x, self.user_agv1_y = agv_position
        elif agv_name == "userAGV2":
            self.user_agv2_x, self.user_agv2_y = agv_position
        elif agv_name == "managerAGV":
            self.manager_agv_x, self.manager_agv_y = agv_position

        # 위치 업데이트
        self.update_agv_position(self.agv1, self.user_agv1_y, self.user_agv1_x)
        self.update_agv_position(self.agv2, self.user_agv2_y, self.user_agv2_x)
        self.update_agv_position(self.agv_admin, self.manager_agv_y, self.manager_agv_x)

        # 좌표 업데이트
        self.lbl_agv1.setText(f"[{self.user_agv1_x}, {self.user_agv1_y}]")     # 고객 AGV1
        self.lbl_agv2.setText(f"[{self.user_agv2_x}, {self.user_agv2_y}]")     # 고객 AGV2
        self.lbl_agv3.setText(f"[{self.manager_agv_x}, {self.manager_agv_y}]") # 관리자 AGV

        # DB에 AGV 위치 업데이트
        self.db_manager.update_agv_position(agv_name, agv_position[0], agv_position[1])

    # DB의 모든 재고를 초기화 하는 함수
    def set_snack_db_init(self):
        for i in range(6):
            label = getattr(self, f"lbl_snack_num{i + 1}")
            label.setText(str(self.snack_num[i]))
            self.db_manager.update_snack_stock(i, self.snack_num[i])

    # 재고 업데이트 함수 (재고를 검사하는 위치에서 해당 함수를 호출해줘야 함)
    def set_snack_stock(self, update_snack_num):
        # 스낵 재고를 검사하는 위치에 manager_agv가 있으면 재고를 파악해서 db에 재고 갯수를 업데이트 함
        
        for idx, (snack_x, snack_y) in enumerate(self.snack_position):
            if self.manager_agv_x == snack_x and self.manager_agv_y == snack_y:
                
                # GUI에 재고 갯수 업데이트
                self.snack_num[idx] = update_snack_num
                label = getattr(self, f"lbl_snack_num{idx + 1}")
                label.setText(str(self.snack_num[idx]))

                # db에 재고 갯수 업데이트
                self.db_manager.update_snack_stock(idx, update_snack_num)
            

    def draw_map(self):
        # 격자맵 생성
        for row in range(6):
            for col in range(7):
                rect = QGraphicsRectItem(col * self.cell_size, row * self.cell_size,
                                         self.cell_size, self.cell_size)
                rect.setBrush(QBrush(Qt.white))
                rect.setPen(Qt.black)
                self.scene.addItem(rect)

        # 벽 생성
        wall = [(1, 1), (1, 3), (1, 5),
                (3, 1), (3, 3), (3, 5),
                (5, 1), (5, 2), (5, 3), (5, 4), (5, 5)]
        # 벽 생성
        for row, col in wall:
            block = QGraphicsRectItem(col * self.cell_size, row * self.cell_size,
                                      self.cell_size, self.cell_size)
            block.setBrush(QBrush(Qt.black))
            self.scene.addItem(block)

    # managerAGV에게 과자 재고 정보를 받는 부분
    def set_snack_num(self):
        pass

    



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ManagerGUI()
    window.show()
    sys.exit(app.exec_())
