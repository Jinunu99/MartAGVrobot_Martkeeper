import cv2
import numpy as np

class LineTracer:
    def __init__(self, roi_boxes=None):
        if roi_boxes is None:
            self.roi_boxes = [
                # (400, 445, 100, 540),
                # (340, 395, 100, 540),
                # (280, 335, 100, 540),
                # (220, 275, 100, 540),
                # (160, 215, 100, 540)
                (240, 285, 100, 540),
                (190, 235, 100, 540),
                (140, 185, 100, 540),
                (90, 135, 100, 540),
                (40, 85, 100, 540)
            ]
        else:
            self.roi_boxes = roi_boxes

        # HSV 마스크 범위 설정 (검정색 선)
        self.lower_hsv = np.array([0, 0, 0])
        self.upper_hsv = np.array([179, 255, 80])

        # ROI 가중치 (하단일수록 높음)
        self.weights = [0.3, 0.26, 0.22, 0.18, 0.14]

    def get_offset(self, frame):
        annotated = frame.copy()
        h, w = frame.shape[:2]
        mid_x = w // 2

        offsets = []
        weighted_sum = 0
        total_weight = 0
        binary = None
        line_presence = []

        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

        for i, (y1, y2, x1, x2) in enumerate(self.roi_boxes):
            roi_hsv = hsv[y1:y2, x1:x2]
            binary = cv2.inRange(roi_hsv, self.lower_hsv, self.upper_hsv)

            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                line_presence.append(False)
                continue

            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) < 300:
                line_presence.append(False)
                continue

            x, y, w_box, h_box = cv2.boundingRect(largest)
            line_cx = x1 + x + w_box // 2
            offset = line_cx - mid_x

            weight = self.weights[i]
            weighted_sum += offset * weight
            total_weight += weight
            line_presence.append(True)

            cv2.rectangle(annotated, (x1 + x, y1 + y), (x1 + x + w_box, y1 + y + h_box), (0, 255, 0), 2)
            cv2.circle(annotated, (line_cx, (y1 + y2) // 2), 4, (255, 255, 255), -1)

        if total_weight == 0:
            return 0, annotated, np.zeros((1, 1), dtype=np.uint8), False, line_presence

        weighted_offset = int(weighted_sum / total_weight)
        return weighted_offset, annotated, binary, True, line_presence

    def get_direction(self, frame):
        offset, annotated, binary, found, presence = self.get_offset(frame)

        # 90도 꺾임 감지: 상단 ROI 2개가 비어 있고, 하단은 감지됨
        if presence[:2] == [False, False] and presence[2:].count(True) >= 2:
            if offset > 30:
                direction = "R90"
            elif offset < -30:
                direction = "L90"
            else:
                direction = "S"

        else:
            if not found:
                direction = "S"
            elif offset < -70:
                direction = "L"
            elif offset > 70:
                direction = "R"
            else:
                direction = "F"

        return direction, offset, annotated, binary, found

    def draw_debug(self, annotated, binary):
        if binary is not None and binary.size > 0:
            binary_color = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            if annotated.shape != binary_color.shape:
                binary_color = cv2.resize(binary_color, (annotated.shape[1], annotated.shape[0]))
            combined = np.hstack((annotated, binary_color))
            return combined
        else:
            return annotated
