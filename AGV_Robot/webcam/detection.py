import cv2
import time
import os
from ultralytics import YOLO
import numpy as np
from collections import deque

from webcam.tracker import ObjectTracker
from webcam.count_reports import print_count_report
from webcam.config import *

class SnackDetector:
    def __init__(self, model_path=MODEL_PATH):
        self.model_path = model_path
        self.model = None
        self.class_names = CLASS_NAMES
        
        # 초기화
        self.cap = None
        self.tracker = None
        self.frame_count = 0
        self.conf_threshold = CONFIDENCE_THRESHOLD
        self.count_history = deque(maxlen=REPORT_CONFIG['max_count_history'])
        
    def initialize_model(self):
        """모델 초기화"""
        print("🤖 모델 로딩 중...")
        self.model = YOLO(self.model_path)
        # 라즈베리파이 최적화
        self.model.to('cpu')  # CPU 명시적 설정
        print("✅ 모델 로드 완료 (CPU 모드)")
        
    def initialize_camera(self):
        """카메라 초기화"""
        print("📹 웹캠 초기화 중...")
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_CONFIG['buffer_size'])
        
        # 라즈베리파이 최적화된 해상도
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_CONFIG['width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_CONFIG['height'])
        
        # MJPEG 코덱으로 압축 효율 향상
        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        self.cap.set(cv2.CAP_PROP_FPS, CAMERA_CONFIG['fps'])
        
        if not self.cap.isOpened():
            raise RuntimeError("❌ 웹캠 열기 실패")
        
        # 실제 해상도 확인
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"📷 실제 해상도: {actual_width}x{actual_height}")
        
        # 워밍업
        print("🔥 웹캠 워밍업...")
        for i in range(CAMERA_CONFIG['warmup_frames']):
            ret, frame = self.cap.read()
            if ret:
                print(f"워밍업 {i+1}/{CAMERA_CONFIG['warmup_frames']}: OK")
            time.sleep(0.1)
            
        return actual_width, actual_height
        
    def initialize_tracker(self):
        """추적기 초기화"""
        self.tracker = ObjectTracker(**TRACKER_CONFIG)
        print("🎯 추적기 초기화 완료")
        
    def detect_objects(self, frame):
        """프레임에서 객체 탐지"""
        try:
            start_time = time.time()
            
            # YOLO 탐지 (전처리 단순화)
            results = self.model(frame, conf=self.conf_threshold, verbose=False, device='cpu')
            
            inference_time = time.time() - start_time
            
            if TERMINAL_CONFIG['show_inference_time']:
                print(f"⏱️ 추론 시간: {inference_time:.3f}초")
            
            # 현재 프레임 탐지 결과
            current_detections = []
            
            if results and len(results) > 0:
                boxes = results[0].boxes
                
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        
                        if class_id < len(self.class_names):
                            class_name = self.class_names[class_id]
                        else:
                            class_name = f"Unknown_{class_id}"
                        
                        current_detections.append({
                            'bbox': (x1, y1, x2, y2),
                            'name': class_name,
                            'confidence': confidence
                        })
                        
                        if TERMINAL_CONFIG['verbose_detection']:
                            # 브랜드_제품명까지 표시 (예: orion_Pocachip)
                            name_parts = class_name.split('_')
                            if len(name_parts) >= 2:
                                display_name = f"{name_parts[0]}_{name_parts[1]}"
                            else:
                                display_name = class_name
                            print(f"🎯 탐지: {display_name} (신뢰도: {confidence:.2f})")
            
            return current_detections
            
        except Exception as e:
            print(f"⚠️ 탐지 오류: {e}")
            return []
    
    def print_detection_summary(self, stable_objects):
        """터미널용 탐지 결과 요약 출력"""
        if not TERMINAL_CONFIG['show_voting_results']:
            return
            
        if not stable_objects:
            print("📊 멀티보팅 결과: 안정화된 객체 없음")
            return
        
        # 클래스별 개수 계산
        class_counts, total_count = self.tracker.get_count_summary()
        
        print(f"\n📊 멀티보팅 결과 (프레임 {self.frame_count}):")
        print(f"  총 객체: {total_count}개")
        
        if class_counts:
            class_summary = []
            for class_name, count in class_counts.items():
                # 브랜드_제품명까지 표시 (예: orion_Pocachip)
                name_parts = class_name.split('_')
                if len(name_parts) >= 2:
                    display_name = f"{name_parts[0]}_{name_parts[1]}"
                else:
                    display_name = class_name
                class_summary.append(f"{display_name}: {count}개")
            print(f"  클래스별: {', '.join(class_summary)}")
        
        # 안정성 정보 (간략하게)
        high_stability = sum(1 for obj in stable_objects if obj['stability'] > 0.8)
        if high_stability > 0:
            print(f"  안정도 높음: {high_stability}개")
        
        print("-" * 50)
            
    def check_control_files(self):
        """파일 기반 제어 확인 (GUI 키입력 대체)"""
        control_dir = CONTROL_CONFIG['control_dir']
        
        # 종료 파일 확인
        quit_file = os.path.join(control_dir, CONTROL_CONFIG['quit_file'])
        if os.path.exists(quit_file):
            os.remove(quit_file)
            print("🔚 종료 신호 감지")
            return 'quit'
        
        # 스크린샷 파일 확인
        screenshot_file = os.path.join(control_dir, CONTROL_CONFIG['screenshot_file'])
        if os.path.exists(screenshot_file):
            os.remove(screenshot_file)
            return 'screenshot'
        
        # 통계 파일 확인
        stats_file = os.path.join(control_dir, CONTROL_CONFIG['stats_file'])
        if os.path.exists(stats_file):
            os.remove(stats_file)
            return 'stats'
        
        # 보고서 파일 확인
        report_file = os.path.join(control_dir, CONTROL_CONFIG['report_file'])
        if os.path.exists(report_file):
            os.remove(report_file)
            return 'report'
        
        # 리셋 파일 확인
        reset_file = os.path.join(control_dir, CONTROL_CONFIG['reset_file'])
        if os.path.exists(reset_file):
            os.remove(reset_file)
            return 'reset'
        
        return None
        
    def handle_control_command(self, command, frame=None):
        """제어 명령 처리"""
        if command == 'quit':
            return False
        elif command == 'screenshot' and frame is not None:
            filename = f"detection_{self.frame_count}_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            print(f"📸 스크린샷 저장: {filename}")
        elif command == 'stats':
            class_counts, total_count = self.tracker.get_count_summary()
            print(f"\n📊 현재 통계:")
            print(f"  프레임: {self.frame_count}")
            print(f"  총 객체: {total_count}개")
            for class_name, count in class_counts.items():
                if count > 0:
                    # 브랜드_제품명까지 표시 (예: orion_Pocachip)
                    name_parts = class_name.split('_')
                    if len(name_parts) >= 2:
                        display_name = f"{name_parts[0]}_{name_parts[1]}"
                    else:
                        display_name = class_name
                    print(f"  {display_name}: {count}개")
        elif command == 'report':
            class_counts, total_count = self.tracker.get_count_summary()
            print_count_report(self.count_history, class_counts, total_count)
        elif command == 'reset':
            self.initialize_tracker()
            print("🔄 추적기 리셋 완료")
        
        return True
        
    def run(self):
        """메인 실행 함수 (터미널 전용)"""
        print("🍪 Level 2 Multi-frame Voting 객체 개수 파악 시스템 (터미널 모드)")
        print("=" * 60)
        
        # 초기화
        self.initialize_model()
        actual_width, actual_height = self.initialize_camera()
        self.initialize_tracker()
        
        print("\n🎯 터미널 모드 객체 개수 파악 시작!")
        print("\n자동 기능:")
        print(f"  통계 출력: 매 {SIMPLE_CONFIG['auto_stats_interval']}프레임마다")
        print(f"  상세 보고서: 매 {SIMPLE_CONFIG['auto_report_interval']}프레임마다")
        print("  종료: Ctrl+C")
        print("=" * 60)
        
        # FPS 측정
        fps_start = time.time()
        fps_counter = 0
        current_fps = 0
        
        try:
            while True:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    print(f"❌ 프레임 {self.frame_count + 1} 읽기 실패")
                    time.sleep(0.1)
                    continue
                
                self.frame_count += 1
                fps_counter += 1
                 
                # FPS 계산
                if fps_counter >= FPS_CONFIG['measurement_interval']:
                    current_time = time.time()
                    current_fps = FPS_CONFIG['measurement_interval'] / (current_time - fps_start)
                    fps_start = current_time
                    fps_counter = 0
                
                # 탐지는 설정된 간격마다
                if self.frame_count % CAMERA_CONFIG['detection_interval'] == 0:
                    print(f"\n🔍 탐지 실행... (프레임 {self.frame_count})")
                    current_detections = self.detect_objects(frame)
                    
                    # 추적기 업데이트 (Level 2 Multi-frame Voting)
                    stable_objects = self.tracker.update(current_detections)
                    
                    # 터미널 출력
                    self.print_detection_summary(stable_objects)
                    
                    # 개수 통계 기록
                    class_counts, total_count = self.tracker.get_count_summary()
                    self.count_history.append({
                        'frame': self.frame_count,
                        'total': total_count,
                        'classes': dict(class_counts)
                    })
                
                # 자동 통계 출력
                if self.frame_count % SIMPLE_CONFIG['auto_stats_interval'] == 0:
                    class_counts, total_count = self.tracker.get_count_summary()
                    print(f"\n📊 자동 통계 (프레임 {self.frame_count}):")
                    print(f"  FPS: {current_fps:.1f}, 총 객체: {total_count}개")
                    for class_name, count in class_counts.items():
                        if count > 0:
                            name_parts = class_name.split('_')
                            if len(name_parts) >= 2:
                                display_name = f"{name_parts[0]}_{name_parts[1]}"
                            else:
                                display_name = class_name
                            print(f"  {display_name}: {count}개")
                
                # 자동 보고서 출력
                if self.frame_count % SIMPLE_CONFIG['auto_report_interval'] == 0 and self.count_history:
                    class_counts, total_count = self.tracker.get_count_summary()
                    print(f"\n📋 자동 보고서 (프레임 {self.frame_count}):")
                    print_count_report(self.count_history, class_counts, total_count)
                
                # 진행상황 주기적 출력
                if self.frame_count % REPORT_CONFIG['progress_report_interval'] == 0:
                    class_counts, total_count = self.tracker.get_count_summary()
                    print(f"\n📈 진행상황: 프레임 {self.frame_count}, FPS {current_fps:.1f}, 총 객체 {total_count}개")
                
                # CPU 부하 감소를 위한 짧은 대기
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n🔚 Ctrl+C로 종료 요청됨")
        
        # 정리
        self.cap.release()
        print("🔚 Level 2 객체 개수 파악 시스템 종료")

# 간단한 실행 함수
def detect_start(model_path=MODEL_PATH):
    """웹캠 객체 탐지 시작 - 터미널 모드"""
    print("🚀 웹캠 객체 탐지 시스템 시작 (터미널 모드)...")
    detector = SnackDetector(model_path=model_path)
    detector.run()

def detect_stop():
    """웹캠 객체 탐지 중지"""
    print("⏹️ 프로그램 종료를 위해서는 Ctrl+C를 사용하세요")