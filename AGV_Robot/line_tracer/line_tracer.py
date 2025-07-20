import cv2
import numpy as np

class LineTracer:
    def __init__(self, roi_boxes=None):
        if roi_boxes is None:
            self.roi_boxes = [
                (400, 445, 100, 540),
                (340, 395, 100, 540),
                (280, 335, 100, 540),
                (220, 275, 100, 540),
                (160, 215, 100, 540)
            ]
        else:
            self.roi_boxes = roi_boxes

        # HSV 마스크 범위 설정
        self.lower_hsv = np.array([0, 0, 0])
        self.upper_hsv = np.array([179, 255, 80])

        # ROI 가중치 (하단이 더 중요, 상단은 덜 중요)
        self.weights = [0.3, 0.3, 0.22, 0.17, 0.11]

    def get_offset(self, frame):
        annotated = frame.copy()
        frame_height, frame_width = frame.shape[:2]
        mid_x = frame_width // 2

        offsets = []
        weighted_sum = 0
        total_weight = 0

        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

        for i, (y1, y2, x1, x2) in enumerate(self.roi_boxes):
            roi_hsv = hsv[y1:y2, x1:x2]
            binary = cv2.inRange(roi_hsv, self.lower_hsv, self.upper_hsv)
            
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                continue

            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)

            if area < 300:
                continue

            x, y, w, h = cv2.boundingRect(largest_contour)
            line_cx = x1 + x + w // 2
            offset = line_cx - mid_x

            # 누적
            weight = self.weights[i]
            weighted_sum += offset * weight
            total_weight += weight

            # 시각화
            cv2.rectangle(annotated, (x1 + x, y1 + y), (x1 + x + w, y1 + y + h), (0, 255, 0), 2)
            cv2.circle(annotated, (line_cx, (y1 + y2) // 2), 4, (255, 255, 255), -1)

        if total_weight == 0:
            return 0, annotated, np.zeros((1, 1), dtype=np.uint8), False

        weighted_offset = int(weighted_sum / total_weight)
        return weighted_offset, annotated, binary, True