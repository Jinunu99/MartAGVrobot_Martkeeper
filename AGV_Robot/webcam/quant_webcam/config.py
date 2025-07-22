# detection/config.py
"""객체 검출 시스템 설정 파일"""

# Coral USB 모델 경로
MODEL_PATH = "webcam/best_full_integer_quant_edgetpu.tflite"
LABELS_PATH = "webcam/labels.txt"

# 웹캠 설정
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 360
BUFFER_SIZE = 1  # 중요: 1로 유지
FPS = 10

# 객체 추적 설정
MAX_HISTORY = 15
MIN_VOTES = 8
IOU_THRESHOLD = 0.3
DISTANCE_THRESHOLD = 50
CONF_THRESHOLD = 0.25

# 클래스명
CLASS_NAMES = [
    'crown_BigPie_Strawberry_324G', 'crown_ChocoHaim_142G', 'crown_Concho_66G',
    'crown_Potto_Cheese_Tart_322G', 'haetae_Guun_Gamja_162G', 'haetae_HoneyButterChip_38G',
    'haetae_Masdongsan_90G', 'haetae_Osajjeu_60G', 'haetae_Oyeseu_360G',
    'lotte_kkokkalkon_gosohanmas_72G', 'nongshim_Alsaeuchip_68G', 'nongshim_Banana_Kick_75G',
    'nongshim_ChipPotato_Original_125G', 'nongshim_Ojingeojip_83G', 'orion_Chocolate_Chip_Cookies_256G',
    'orion_Diget_Choco_312G', 'orion_Diget_tongmil_28_194G', 'orion_Fresh_Berry_336G',
    'orion_Gosomi_80G', 'orion_Pocachip_Original_66G', 'orion_chokchokhan_Chocochip_240G'
]