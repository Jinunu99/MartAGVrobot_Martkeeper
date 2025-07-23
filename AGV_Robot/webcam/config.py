# PyTorch 호환성 설정
import os
os.environ['PYTORCH_DISABLE_WEIGHTS_ONLY'] = '1'

# 모델 설정
MODEL_PATH = "./epoch60.pt"
CONFIDENCE_THRESHOLD = 0.4  # 라즈베리파이 최적화를 위해 높임

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

# 추적기 설정 (라즈베리파이 최적화)
TRACKER_CONFIG = {
    'max_history': 7,           # 15 → 7 (메모리 절약)
    'min_votes': 4,             # 8 → 4 (빠른 결론)
    'iou_threshold': 0.3,       # IoU 임계값 (같은 객체 판정)
    'distance_threshold': 50    # 거리 임계값 (픽셀)
}

# 15회 관찰 설정
OBSERVATION_CONFIG = {
    'max_observations': 15,     # 총 관찰 횟수
    'show_progress': True       # 진행상황 표시
}

# 카메라 설정 (라즈베리파이 최적화)
CAMERA_CONFIG = {
    'width': 640,               # 640 웹캡 해상도에 맞게 적용
    'height': 360,              # 360 웹캡 해상도에 맞게 적용
    'fps': 6,                   # 10 → 6 (CPU 부하 감소)
    'buffer_size': 1,           # 버퍼 크기
    'detection_interval': 5,    # 5프레임마다 디텍션
    'warmup_frames': 3          # 3 (빠른 시작)
}

# 간단한 실행 설정
SIMPLE_CONFIG = {
    'auto_stats_interval': 100,     # 자동 통계 출력 간격 (프레임)
    'auto_report_interval': 300     # 자동 보고서 출력 간격 (프레임)
}

# 안정성 임계값
STABILITY_THRESHOLDS = {
    'very_stable': 0.8,
    'stable': 0.6,
    'moderate': 0.4
}

# 보고서 설정 (메모리 최적화)
REPORT_CONFIG = {
    'max_count_history': 50,        # 100 → 50 (메모리 절약)
    'recent_frames_analysis': 15,   # 20 → 15
    'progress_report_interval': 50  # 100 → 50 (더 자주 출력)
}

# FPS 측정 설정
FPS_CONFIG = {
    'measurement_interval': 20       # 30 → 20 (더 자주 측정)
}

# 신뢰도 조절 설정
CONFIDENCE_CONFIG = {
    'min_threshold': 0.4,    
    'max_threshold': 0.9,
    'adjustment_step': 0.05
}

# 터미널 출력 설정
TERMINAL_CONFIG = {
    'verbose_detection': True,      # 개별 탐지 결과 출력 여부
    'show_inference_time': True,    # 추론 시간 출력 여부
    'show_voting_results': True,    # 멀티보팅 결과 출력 여부
    'compact_output': False         # 간결한 출력 모드
}