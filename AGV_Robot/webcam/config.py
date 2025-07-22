# PyTorch 호환성 설정
import os
os.environ['PYTORCH_DISABLE_WEIGHTS_ONLY'] = '1'

# 모델 설정
MODEL_PATH = "./best.pt"
CONFIDENCE_THRESHOLD = 0.25

# 클래스명 정의
CLASS_NAMES = [
    'crown_BigPie_Strawberry_324G', 'crown_ChocoHaim_142G', 'crown_Concho_66G',
    'crown_Potto_Cheese_Tart_322G', 'haetae_Guun_Gamja_162G', 'haetae_HoneyButterChip_38G',
    'haetae_Masdongsan_90G', 'haetae_Osajjeu_60G', 'haetae_Oyeseu_360G',
    'lotte_kkokkalkon_gosohanmas_72G', 'nongshim_Alsaeuchip_68G', 'nongshim_Banana_Kick_75G',
    'nongshim_ChipPotato_Original_125G', 'nongshim_Ojingeojip_83G', 'orion_Chocolate_Chip_Cookies_256G',
    'orion_Diget_Choco_312G', 'orion_Diget_tongmil_28_194G', 'orion_Fresh_Berry_336G',
    'orion_Gosomi_80G', 'orion_Pocachip_Original_66G', 'orion_chokchokhan_Chocochip_240G'
]

# 추적기 설정
TRACKER_CONFIG = {
    'max_history': 15,      # 최대 히스토리 프레임 수
    'min_votes': 8,         # 최소 투표 수 (유효 객체 판정)
    'iou_threshold': 0.3,   # IoU 임계값 (같은 객체 판정)
    'distance_threshold': 50 # 거리 임계값 (픽셀)
}

# 카메라 설정
CAMERA_CONFIG = {
    'width': 320,           # 프레임 너비
    'height': 320,          # 프레임 높이  
    'fps': 10,              # 프레임률
    'buffer_size': 1,       # 버퍼 크기
    'detection_interval': 10, # 탐지 실행 간격 (프레임)
    'warmup_frames': 10     # 워밍업 프레임 수
}

# UI 설정
UI_CONFIG = {
    'window_name': 'Level 2 Object Counting System',
    'window_width': 800,
    'window_height': 600,
    'font_scale': 0.7,
    'font_thickness': 2,
    'gui_test_duration': 2000  # 밀리초
}

# 색상 설정 (BGR 형식)
COLORS = {
    'very_stable': (0, 255, 0),      # 매우 안정: 초록색
    'stable': (0, 255, 255),         # 안정: 노란색  
    'moderate': (0, 165, 255),       # 보통: 주황색
    'unstable': (255, 0, 255),       # 불안정: 보라색
    'text': (255, 255, 255),         # 텍스트: 흰색
    'count_text': (0, 255, 0),       # 개수 텍스트: 초록색
    'class_text': (255, 255, 0),     # 클래스 텍스트: 노란색
    'error': (0, 0, 255)             # 에러: 빨간색
}

# 안정성 임계값
STABILITY_THRESHOLDS = {
    'very_stable': 0.8,
    'stable': 0.6,
    'moderate': 0.4
}

# 보고서 설정
REPORT_CONFIG = {
    'max_count_history': 100,        # 최대 개수 히스토리 보관
    'recent_frames_analysis': 20,    # 최근 프레임 분석 개수
    'progress_report_interval': 100  # 진행상황 출력 간격
}

# FPS 측정 설정
FPS_CONFIG = {
    'measurement_interval': 30       # FPS 측정 간격 (프레임)
}

# 키 매핑
KEY_MAPPINGS = {
    'quit': ord('q'),
    'screenshot': ord(' '),
    'statistics': ord('s'), 
    'increase_conf': [ord('+'), ord('=')],
    'decrease_conf': ord('-'),
    'reset_tracker': ord('r'),
    'count_report': ord('c')
}

# 신뢰도 조절 설정
CONFIDENCE_CONFIG = {
    'min_threshold': 0.1,
    'max_threshold': 0.9,
    'adjustment_step': 0.05
}