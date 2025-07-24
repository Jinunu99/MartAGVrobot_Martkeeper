import cv2
import numpy as np
from picamera2 import Picamera2

# 초기 HSV 범위
lower = np.array([0, 0, 0])
upper = np.array([179, 255, 255])

def nothing(x):
    pass

# 트랙바 윈도우 생성
cv2.namedWindow("Trackbars")
cv2.createTrackbar("H Lower", "Trackbars", 0, 179, nothing)
cv2.createTrackbar("S Lower", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("V Lower", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("H Upper", "Trackbars", 179, 179, nothing)
cv2.createTrackbar("S Upper", "Trackbars", 255, 255, nothing)
cv2.createTrackbar("V Upper", "Trackbars", 255, 255, nothing)

# 카메라 초기화
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
picam2.configure(preview_config)
picam2.start()

# 클릭 기반 HSV 추출
def pick_color(event, x, y, flags, param):
    global lower, upper
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv_value = param[y, x]
        print(f"[클릭 HSV] H: {hsv_value[0]}, S: {hsv_value[1]}, V: {hsv_value[2]}")
        h, s, v = hsv_value
        lower = np.array([max(0, h - 10), max(0, s - 40), max(0, v - 40)])
        upper = np.array([min(179, h + 10), min(255, s + 40), min(255, v + 40)])

cv2.namedWindow("Original")
cv2.setMouseCallback("Original", lambda event, x, y, flags, _: pick_color(event, x, y, flags, hsv))

while True:
    frame = picam2.capture_array()
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

    # 트랙바 HSV 범위 업데이트
    h1 = cv2.getTrackbarPos("H Lower", "Trackbars")
    s1 = cv2.getTrackbarPos("S Lower", "Trackbars")
    v1 = cv2.getTrackbarPos("V Lower", "Trackbars")
    h2 = cv2.getTrackbarPos("H Upper", "Trackbars")
    s2 = cv2.getTrackbarPos("S Upper", "Trackbars")
    v2 = cv2.getTrackbarPos("V Upper", "Trackbars")

    lower = np.array([h1, s1, v1])
    upper = np.array([h2, s2, v2])

    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # 결과 출력
    cv2.imshow("Original", frame)
    cv2.imshow("Mask", mask)
    cv2.imshow("Result", result)

    key = cv2.waitKey(1)
    if key == ord('q') or key == 27:
        break

cv2.destroyAllWindows()
picam2.close()
