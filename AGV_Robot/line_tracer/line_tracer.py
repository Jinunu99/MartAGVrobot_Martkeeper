import cv2
import numpy as np

class LineTracer:
    def __init__(self, roi_box=(380, 480, 100, 540)):
        # ROI 범위를 설정합니다 (y1, y2, x1, x2)
        self.y1, self.y2, self.x1, self.x2 = roi_box

    def get_direction(self, frame):
        roi = frame[self.y1:self.y2, self.x1:self.x2]
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)

        # 이진화 (Threshold): 밝기 기준 이하(검정색)을 흰색(255)으로 반전 추출
        # 검정색 라인을 강조하기 위해 THRESH_BINARY_INV 사용
        _, binary = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)

        # 모멘트를 통해 검출된 흰색 영역(라인)의 중심좌표(cx, cy)를 계산
        M = cv2.moments(binary)

        # 검출된 흰색 영역이 없으면 (m00 == 0), 라인이 사라졌다고 판단
        if M['m00'] == 0:
            return "S", frame, binary  # 방향: S = Stop

        # 중심점 X좌표 계산 (무게중심 공식)
        cx = int(M['m10'] / M['m00'])

        # ROI의 정중앙 기준점 X좌표 (프레임 중앙과 비교할 기준)
        mid_x = (self.x2 - self.x1) // 2

        # === 디버깅 시각화 영역 ===

        cv2.circle(roi, (cx, 50), 5, (0, 255, 0), -1)
        cv2.line(roi, (mid_x, 0), (mid_x, 100), (255, 0, 0), 2)
        cv2.line(roi, (mid_x, 50), (cx, 50), (0, 0, 255), 2)

        # === 방향 판단 ===

        if cx < mid_x - 40:
            return "L", frame, binary
        elif cx > mid_x + 40:
            # 중심이 오른쪽으로 치우쳐 있으면 → 오른쪽 회전
            return "R", frame, binary
        else:
            # 중심이 중앙 근처에 있음 → 전진
            return "F", frame, binary
