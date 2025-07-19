# config.py - 설정 파일

# 모델 설정
MODEL_PATH = "/home/paper/workspace/MartAGVrobot_Martkeeper/model/best.pt"

# 클래스명 정의
CLASS_NAMES = [
    "Alsaeuchip", "BananaKick", "CaramelCornMaple", "Cheetos", "CornChips",
    "Gamjakkang", "Jjanggu", "JollyPong", "Kkobugchip", "Kkochgelang",
    "Kkulkkwabaegi", "KokkalCorn", "Koncho", "Matdongsan", "Ogamja",
    "Pocachip_Onion", "Pocachip_Original", "Postick", "Saeukkang",
    "Sunchip", "Swingchip", "Yangpaling", "konchi"
]

# 웹캠 설정
WEBCAM_CONFIG = {
    'width': 320,
    'height': 240,
    'fps': 10,
    'buffer_size': 1
}

# 탐지 설정
DETECTION_CONFIG = {
    'conf_threshold': 0.2,
    'detection_interval': 3,  # 매 N프레임마다 탐지
    'stabilization_frames': 5,  # 안정화를 위한 프레임 수
    'min_stable_count': 2  # 안정화 최소 탐지 횟수
}

# 화면 설정
DISPLAY_CONFIG = {
    'window_name': 'Snack Detection',
    'display_width': 640,
    'display_height': 480
}

# 색상 설정 (BGR)
COLORS = {
    'high_conf': (0, 255, 0),      # 높은 신뢰도: 초록색
    'medium_conf': (0, 255, 255),  # 중간 신뢰도: 노란색
    'low_conf': (0, 165, 255),     # 낮은 신뢰도: 주황색
    'text': (255, 255, 255),       # 텍스트: 흰색
    'error': (0, 0, 255),          # 에러: 빨간색
    'success': (0, 255, 0)         # 성공: 초록색
}