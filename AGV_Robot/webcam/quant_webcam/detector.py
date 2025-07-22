# detection/detector.py
"""객체 검출 시스템 메인 클래스 - 팀 프로젝트 통합용"""

import cv2
import time
import numpy as np
import threading
from collections import deque

from .webcam.quant_webcam.config import *
from .coral_detector import CoralDetector
from .object_tracker import ObjectTracker

class ObjectDetectionSystem:
    """객체 검출 시스템 클래스 - 다른 모듈에서 호출 가능"""
    
    def __init__(self, model_path=None, labels_path=None, config_override=None):
        """
        초기화
        Args:
            model_path: 모델 파일 경로 (기본값: config.py 사용)
            labels_path: 라벨 파일 경로 (기본값: config.py 사용)
            config_override: 설정 오버라이드 dict
        """
        # 설정 적용
        if config_override:
            for key, value in config_override.items():
                if hasattr(globals(), key):
                    globals()[key] = value
        
        # 모델 경로
        self.model_path = model_path or MODEL_PATH
        self.labels_path = labels_path or LABELS_PATH
        
        # 컴포넌트 초기화
        self.detector = None
        self.tracker = None
        self.cap = None
        
        # 상태 변수
        self.is_running = False
        self.is_initialized = False
        self.frame_count = 0
        self.current_fps = 0
        self.conf_threshold = CONF_THRESHOLD
        
        # 최신 결과 저장
        self.latest_frame = None
        self.latest_objects = []
        self.latest_counts = {}
        self.latest_total = 0
        
        # 스레드 관리
        self.detection_thread = None
        self.lock = threading.Lock()
        
    def initialize(self):
        """시스템 초기화"""
        try:
            print("🤖 객체 검출 시스템 초기화 중...")
            
            # 모델 로드
            self.detector = CoralDetector(self.model_path, self.labels_path)
            
            # 추적기 초기화
            self.tracker = ObjectTracker(
                max_history=MAX_HISTORY,
                min_votes=MIN_VOTES,
                iou_threshold=IOU_THRESHOLD,
                distance_threshold=DISTANCE_THRESHOLD
            )
            
            # 웹캠 초기화
            self.cap = self._init_camera()
            if self.cap is None:
                raise Exception("웹캠 초기화 실패")
            
            self.is_initialized = True
            print("✅ 객체 검출 시스템 초기화 완료")
            return True
            
        except Exception as e:
            print(f"❌ 초기화 실패: {e}")
            return False
    
    def _init_camera(self):
        """웹캠 초기화"""
        print("📹 웹캠 초기화 중...")
        cap = cv2.VideoCapture(CAMERA_INDEX)
        
        # 중요: 버퍼 사이즈 1로 설정
        cap.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER_SIZE)
        
        # 해상도 및 FPS 설정
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, FPS)
        
        # MJPEG 코덱
        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        
        if not cap.isOpened():
            return None
        
        # 워밍업
        for i in range(3):
            ret, frame = cap.read()
            if ret:
                print(f"웹캠 워밍업 {i+1}: OK")
        
        return cap
    
    def start_detection(self, show_window=True):
        """검출 시작 (스레드 기반)"""
        if not self.is_initialized:
            if not self.initialize():
                return False
        
        if self.is_running:
            print("이미 실행 중입니다.")
            return True
        
        self.is_running = True
        self.detection_thread = threading.Thread(
            target=self._detection_loop, 
            args=(show_window,)
        )
        self.detection_thread.daemon = True
        self.detection_thread.start()
        
        print("🎯 객체 검출 시작!")
        return True
    
    def stop_detection(self):
        """검출 중지"""
        self.is_running = False
        
        if self.detection_thread:
            self.detection_thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        print("🔚 객체 검출 중지")
    
    def _detection_loop(self, show_window=True):
        """검출 루프 (내부 함수)"""
        fps_start = time.time()
        fps_counter = 0
        
        # 윈도우 생성 (필요시)
        if show_window:
            window_name = 'Object Detection'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        while self.is_running:
            ret, frame = self.cap.read()
            
            if not ret:
                print("❌ 프레임 읽기 실패")
                continue
            
            self.frame_count += 1
            fps_counter += 1
            
            # FPS 계산
            if fps_counter >= 30:
                current_time = time.time()
                self.current_fps = 30 / (current_time - fps_start)
                fps_start = current_time
                fps_counter = 0
            
            # 매 3프레임마다 검출
            if self.frame_count % 3 == 0:
                try:
                    # 검출 수행
                    detections, inference_time = self.detector.detect(frame, self.conf_threshold)
                    
                    # 추적기 업데이트
                    stable_objects = self.tracker.update(detections)
                    
                    # 결과 업데이트 (스레드 안전)
                    with self.lock:
                        self.latest_frame = frame.copy()
                        self.latest_objects = stable_objects.copy()
                        self.latest_counts, self.latest_total = self.tracker.get_count_summary()

                    # ✅ 클래스별 개수 출력
                    if self.latest_counts:
                        print("📦 클래스별 검출 결과:")
                        for cls, count in self.latest_counts.items():
                            print(f"  - {cls}: {count}개")
                        print(f"🔢 총 객체 수: {self.latest_total}\n")
                    
                except Exception as e:
                    print(f"⚠️ 검출 오류: {e}")
            
            # 화면 표시 (필요시)
            if show_window:
                display_frame = self._draw_objects(frame.copy())
                cv2.imshow(window_name, display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.stop_detection()
                    break
    
    def _draw_objects(self, frame):
        """객체 그리기"""
        with self.lock:
            objects = self.latest_objects.copy()
            counts = self.latest_counts.copy()
            total = self.latest_total
        
        # 객체 그리기
        for obj in objects:
            x1, y1, x2, y2 = obj['bbox']
            class_name = obj['name']
            confidence = obj['confidence']
            stability = obj['stability']
            
            # 색상
            if stability > 0.8:
                color = (0, 255, 0)
            elif stability > 0.6:
                color = (0, 255, 255)
            else:
                color = (0, 165, 255)
            
            # 박스와 라벨
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            short_name = class_name.split('_')[0] if '_' in class_name else class_name[:8]
            label = f"{short_name} {confidence:.2f}"
            cv2.putText(frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # 정보 표시
        cv2.putText(frame, f"Frame: {self.frame_count}", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"FPS: {self.current_fps:.1f}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"Objects: {total}", (10, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        return frame
    
    def get_current_results(self):
        """현재 검출 결과 반환 (다른 모듈에서 호출)"""
        with self.lock:
            return {
                'frame': self.latest_frame.copy() if self.latest_frame is not None else None,
                'objects': self.latest_objects.copy(),
                'class_counts': self.latest_counts.copy(),
                'total_count': self.latest_total,
                'fps': self.current_fps,
                'frame_number': self.frame_count
            }
    
    def get_object_counts(self):
        """객체 개수만 반환 (간단한 API)"""
        with self.lock:
            return self.latest_counts.copy(), self.latest_total
    
    def set_confidence_threshold(self, threshold):
        """신뢰도 임계값 설정"""
        self.conf_threshold = max(0.1, min(0.9, threshold))
        print(f"신뢰도 임계값: {self.conf_threshold:.2f}")
    
    def reset_tracker(self):
        """추적기 리셋"""
        if self.tracker:
            self.tracker.reset()
            print("🔄 추적기 리셋")
    
    def is_detection_running(self):
        """검출 실행 상태 확인"""
        return self.is_running
    
    def get_system_status(self):
        """시스템 상태 반환"""
        return {
            'initialized': self.is_initialized,
            'running': self.is_running,
            'fps': self.current_fps,
            'frame_count': self.frame_count,
            'conf_threshold': self.conf_threshold
        }

def run_standalone():
    """독립 실행 함수"""
    print("🍪 Coral USB 객체 검출 시스템 (독립 실행)")
    
    # 시스템 생성
    detection_system = ObjectDetectionSystem()
    
    # 초기화 및 실행
    if detection_system.initialize():
        try:
            detection_system.start_detection(show_window=True)
            
            print("키 조작:")
            print("  'q': 종료")
            print("  'SPACE': 결과 출력")
            
            # 메인 루프 (결과 모니터링)
            while detection_system.is_detection_running():
                time.sleep(1)
                
                # 주기적 상태 출력
                if detection_system.frame_count % 100 == 0:
                    results = detection_system.get_current_results()
                    print(f"📊 진행: {results['frame_number']}프레임, "
                          f"FPS {results['fps']:.1f}, "
                          f"객체 {results['total_count']}개")
        
        except KeyboardInterrupt:
            print("\n사용자 중단")
        
        finally:
            detection_system.stop_detection()
    
    else:
        print("❌ 시스템 초기화 실패")

if __name__ == "__main__":
    run_standalone()