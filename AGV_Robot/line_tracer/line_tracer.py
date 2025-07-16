import cv2
import numpy as np

class LineTracer:
    def __init__(self, roi_boxes=None):
        # 여러 ROI 박스 설정 (y1, y2, x1, x2)
        if roi_boxes is None:
            self.roi_boxes = [
                (400, 440, 100, 540),  # 하단
                (340, 390, 100, 540),  # 중간
                (280, 330, 100, 540)   # 상단
            ]
        else:
            self.roi_boxes = roi_boxes

    def get_direction(self, frame):
        cx_list = []
        annotated = frame.copy()

        for (y1, y2, x1, x2) in self.roi_boxes:
            roi = frame[y1:y2, x1:x2]
            gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV) # 100, 255

            M = cv2.moments(binary)
            if M['m00'] == 0:
                cx_list.append(None)
                continue

            cx = int(M['m10'] / M['m00'])
            cx_list.append(cx)

            # 시각화: 박스와 중심점
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.circle(annotated, (x1 + cx, (y1 + y2)//2), 5, (0, 0, 255), -1)

        # ROI 중심점 연결 시각화
        for i in range(1, len(cx_list)):
            if cx_list[i] is not None and cx_list[i - 1] is not None:
                y_prev = (self.roi_boxes[i - 1][0] + self.roi_boxes[i - 1][1]) // 2
                y_curr = (self.roi_boxes[i][0] + self.roi_boxes[i][1]) // 2
                x_prev = self.roi_boxes[i - 1][2] + cx_list[i - 1]
                x_curr = self.roi_boxes[i][2] + cx_list[i]
                cv2.line(annotated, (x_prev, y_prev), (x_curr, y_curr), (0, 255, 255), 2)

        # 중심값이 하나도 없으면 멈춤
        valid_cx = [c for c in cx_list if c is not None]
        if not valid_cx:
            return "S", annotated, None

        # 평균 중심값과 중간 기준점
        avg_cx = np.mean(valid_cx)
        mid_x = (self.roi_boxes[0][3] - self.roi_boxes[0][2]) // 2

        # 복합 방향 판단을 위한 delta 계산
        direction = "F"  # 기본: 직진
        if len(valid_cx) >= 2:
            deltas = [valid_cx[i] - valid_cx[i - 1] for i in range(1, len(valid_cx)) if valid_cx[i - 1] is not None]

            avg_delta = np.mean(deltas) if deltas else 0

            if avg_delta > 50:
                direction = "R"
            elif avg_delta > 20:
                direction = "RF"
            elif avg_delta < -50:
                direction = "L"
            elif avg_delta < -20:
                direction = "LF"

        # 중앙 기준으로 추가 보정 (중간 중심값 기준)
        if avg_cx < mid_x - 50:
            direction = "L"
        elif avg_cx < mid_x - 20:
            direction = "LF"
        elif avg_cx > mid_x + 50:
            direction = "R"
        elif avg_cx > mid_x + 20:
            direction = "RF"

        return direction, annotated, binary
