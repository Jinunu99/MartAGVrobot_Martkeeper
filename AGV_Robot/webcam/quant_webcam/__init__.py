# detection/__init__.py
"""
객체 검출 모듈 - 팀 프로젝트 통합용 간단한 API
사용법:
    from detection import start_detect, stop_detect, get_results
    start_detect()  # 검출 시작
    results = get_results()  # 결과 가져오기
    stop_detect()  # 검출 종료
"""

from .detector import ObjectDetectionSystem

# 전역 검출 시스템 인스턴스
_detection_system = None

def start_detect(show_window=False, model_path=None, config_override=None):
    """
    객체 검출 시작 (한 줄 호출)
    
    Args:
        show_window (bool): GUI 창 표시 여부 (기본: False)
        model_path (str): 커스텀 모델 경로
        config_override (dict): 설정 오버라이드
    
    Returns:
        bool: 성공 여부
    """
    global _detection_system
    
    try:
        if _detection_system is None:
            _detection_system = ObjectDetectionSystem(
                model_path=model_path,
                config_override=config_override
            )
        
        if not _detection_system.is_detection_running():
            success = _detection_system.start_detection(show_window=show_window)
            if success:
                print("✅ 객체 검출 시작됨")
            return success
        else:
            print("⚠️ 이미 검출이 실행 중입니다")
            return True
            
    except Exception as e:
        print(f"❌ 검출 시작 실패: {e}")
        return False

def stop_detect():
    """객체 검출 중지 (한 줄 호출)"""
    global _detection_system
    
    if _detection_system and _detection_system.is_detection_running():
        _detection_system.stop_detection()
        print("✅ 객체 검출 중지됨")
    else:
        print("⚠️ 검출이 실행되고 있지 않습니다")

def get_results():
    """
    현재 검출 결과 가져오기
    
    Returns:
        dict: {
            'objects': [객체 리스트],
            'class_counts': {클래스: 개수},
            'total_count': 총개수,
            'fps': FPS,
            'frame_number': 프레임번호
        } 또는 None (검출 중이 아닐 때)
    """
    global _detection_system
    
    if _detection_system and _detection_system.is_detection_running():
        return _detection_system.get_current_results()
    else:
        return None

def get_counts():
    """
    객체 개수만 간단히 가져오기
    
    Returns:
        tuple: (class_counts_dict, total_count) 또는 (None, 0)
    """
    global _detection_system
    
    if _detection_system and _detection_system.is_detection_running():
        return _detection_system.get_object_counts()
    else:
        return None, 0

def is_running():
    """검출 실행 상태 확인"""
    global _detection_system
    return _detection_system is not None and _detection_system.is_detection_running()

def set_confidence(threshold):
    """신뢰도 임계값 설정"""
    global _detection_system
    if _detection_system:
        _detection_system.set_confidence_threshold(threshold)

def reset_tracker():
    """추적기 리셋"""
    global _detection_system
    if _detection_system:
        _detection_system.reset_tracker()

def get_status():
    """시스템 상태 확인"""
    global _detection_system
    if _detection_system:
        return _detection_system.get_system_status()
    else:
        return {'initialized': False, 'running': False}

# 편의 함수들
def quick_start():
    """빠른 시작 (기본 설정으로)"""
    return start_detect(show_window=False)

def start_with_gui():
    """GUI와 함께 시작"""
    return start_detect(show_window=True)

def get_object_list():
    """검출된 객체 리스트만 반환"""
    results = get_results()
    return results['objects'] if results else []

def get_total_count():
    """총 객체 개수만 반환"""
    _, total = get_counts()
    return total

# 모듈 정보
__version__ = "1.0.0"
__author__ = "Team Project"
__description__ = "Coral USB 기반 객체 검출 시스템"

# 공개 API
__all__ = [
    # 메인 API
    'start_detect',
    'stop_detect', 
    'get_results',
    'get_counts',
    'is_running',
    
    # 설정 API
    'set_confidence',
    'reset_tracker',
    'get_status',
    
    # 편의 함수
    'quick_start',
    'start_with_gui',
    'get_object_list',
    'get_total_count'
]