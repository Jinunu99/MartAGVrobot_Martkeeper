# utils.py - 유틸리티 함수들

import cv2
import numpy as np
from config import COLORS, DETECTION_CONFIG


def test_gui():
    """GUI 기본 테스트"""
    print("🧪 GUI 기본 테스트...")
    test_img = np.zeros((200, 400, 3), dtype=np.uint8)
    test_img[50:150, 50:350] = [0, 255, 0]
    cv2.putText(test_img, "GUI Working!", (100, 110), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    cv2.namedWindow('GUI Test', cv2.WINDOW_NORMAL)
    cv2.imshow('GUI Test', test_img)
    print("GUI 테스트 창이 보이나요? 2초 후 자동으로 닫힙니다.")
    cv2.waitKey(2000)
    cv2.destroyAllWindows()


def stabilize_detections(detection_history, class_names):
    """탐지 결과 안정화"""
    if not detection_history:
        return []
    
    # 클래스별로 탐지 빈도 계산
    class_count = {}
    class_positions = {}
    
    for detections in detection_history:
        for detection in detections:
            class_name = detection['name']
            bbox = detection['bbox']
            confidence = detection['confidence']
            
            if class_name not in class_count:
                class_count[class_name] = 0
                class_positions[class_name] = []
            
            class_count[class_name] += 1
            class_positions[class_name].append({
                'bbox': bbox,
                'confidence': confidence
            })
    
    # 안정화된 결과 생성 (최소 2번 이상 탐지된 것만)
    stable_results = []
    min_count = DETECTION_CONFIG['min_stable_count']
    
    for class_name, count in class_count.items():
        if count >= min_count:  # 최소 탐지 횟수 이상
            positions = class_positions[class_name]
            
            # 평균 위치와 최고 신뢰도 계산
            avg_x1 = sum([pos['bbox'][0] for pos in positions]) // len(positions)
            avg_y1 = sum([pos['bbox'][1] for pos in positions]) // len(positions)
            avg_x2 = sum([pos['bbox'][2] for pos in positions]) // len(positions)
            avg_y2 = sum([pos['bbox'][3] for pos in positions]) // len(positions)
            
            max_confidence = max([pos['confidence'] for pos in positions])
            
            stable_results.append({
                'bbox': (avg_x1, avg_y1, avg_x2, avg_y2),
                'name': class_name,
                'confidence': max_confidence
            })
    
    return stable_results


def get_confidence_color(confidence):
    """신뢰도에 따른 색상 반환"""
    if confidence > 0.7:
        return COLORS['high_conf']
    elif confidence > 0.4:
        return COLORS['medium_conf']
    else:
        return COLORS['low_conf']


def draw_detections(frame, detections):
    """탐지 결과를 프레임에 그리기"""
    for detection in detections:
        x1, y1, x2, y2 = detection['bbox']
        class_name = detection['name']
        confidence = detection['confidence']
        
        color = get_confidence_color(confidence)
        
        # 바운딩 박스
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # 라벨
        label = f"{class_name}: {confidence:.2f}"
        cv2.putText(frame, label, (x1, y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    return frame


def draw_status_info(frame, frame_count, fps, detections_count, conf_threshold, 
                    stabilization_mode, camera_ok, width, height):
    """상태 정보를 프레임에 그리기"""
    # 기본 상태 정보
    cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS['text'], 2)
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS['text'], 2)
    cv2.putText(frame, f"Objects: {detections_count}", (10, 90), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS['text'], 2)
    cv2.putText(frame, f"Conf: {conf_threshold:.2f}", (10, 120), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS['text'], 2)
    cv2.putText(frame, f"Stable: {'ON' if stabilization_mode else 'OFF'}", (10, 150), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
               COLORS['success'] if stabilization_mode else COLORS['error'], 2)
    
    # 카메라 상태 표시
    status_color = COLORS['success'] if camera_ok else COLORS['error']
    status_text = "CAM OK" if camera_ok else "CAM ERROR"
    cv2.putText(frame, status_text, (width-150, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    
    return frame


def create_error_frame(width, height, message="CAMERA ERROR"):
    """에러 프레임 생성"""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(frame, message, (width//2-100, height//2), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, COLORS['error'], 3)
    return frame


def preprocess_frame(frame):
    """프레임 전처리"""
    # 간단한 대비 개선
    processed_frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=5)
    return processed_frame


def print_help():
    """도움말 출력"""
    print("🎯 과자 탐지 시작!")
    print("주요 조작:")
    print("  'q': 종료")
    print("  'SPACE': 스크린샷")
    print("  's': 상태 확인")
    print("  '+/-': 신뢰도 조절")
    print("  'f': 안정화 모드 토글")