import cv2
import time
import os
from datetime import datetime
from ultralytics import YOLO
import numpy as np
from collections import deque, Counter

from webcam.tracker import ObjectTracker
from webcam.count_reports import print_final_report
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
        
        # 관찰 관련 변수들
        self.observation_count = 0  # 현재 관찰 횟수
        self.observation_results = []  # 각 관찰의 결과 저장
        self.max_observations = OBSERVATION_CONFIG['max_observations']
        
        # 최종 결과 저장
        self.final_results = None
        
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
        
        print(f"\n📊 멀티보팅 결과 (관찰 {self.observation_count}/{self.max_observations}):")
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
    
    def print_observation_progress(self):
        """관찰 진행상황 출력"""
        if not OBSERVATION_CONFIG['show_progress']:
            return
            
        progress_bar = "█" * self.observation_count + "░" * (self.max_observations - self.observation_count)
        print(f"\n🎯 관찰 진행상황:")
        print(f"  진행: [{progress_bar}] {self.observation_count}/{self.max_observations}")
        
    def record_observation_result(self):
        """현재 관찰 결과 기록"""
        class_counts, total_count = self.tracker.get_count_summary()
        
        observation_result = {
            'observation_number': self.observation_count,
            'total_count': total_count,
            'class_counts': dict(class_counts),
            'timestamp': datetime.now().isoformat()
        }
        
        self.observation_results.append(observation_result)
        print(f"📝 관찰 {self.observation_count} 결과 기록 완료")
    
    def analyze_final_results(self):
        """관찰 완료 후 빈도 기반 최종 분석"""
        print("\n" + "="*60)
        print(f"📊 {self.max_observations}회 관찰 완료 - 빈도 기반 최종 분석")
        print("="*60)
        
        if not self.observation_results:
            print("❌ 관찰 결과가 없습니다.")
            self.final_results = {}
            return self.final_results
        
        # 모든 등장한 클래스 수집
        all_classes = set()
        for result in self.observation_results:
            all_classes.update(result['class_counts'].keys())
        
        final_results = {}
        total_products = 0
        
        print("🔍 클래스별 빈도 분석:")
        
        for class_name in all_classes:
            # 각 클래스의 개수별 빈도 계산
            count_frequency = Counter()
            for result in self.observation_results:
                count = result['class_counts'].get(class_name, 0)
                count_frequency[count] += 1
            
            # 가장 빈번한 개수 선택
            most_frequent_count = count_frequency.most_common(1)[0][0]
            frequency_score = count_frequency[most_frequent_count] / len(self.observation_results)
            
            if most_frequent_count > 0:  # 0개가 아닌 경우만
                final_results[class_name] = {
                    'count': most_frequent_count,
                    'frequency_score': frequency_score,
                    'appeared_in': sum(1 for r in self.observation_results if r['class_counts'].get(class_name, 0) > 0)
                }
                total_products += most_frequent_count
                
                # 브랜드_제품명까지 표시
                name_parts = class_name.split('_')
                display_name = f"{name_parts[0]}_{name_parts[1]}" if len(name_parts) >= 2 else class_name
                
                print(f"  ✅ {display_name}: {most_frequent_count}개 (빈도: {frequency_score:.2f}, 등장: {final_results[class_name]['appeared_in']}/{self.max_observations}회)")
        
        print(f"\n📋 최종 결과:")
        print(f"  총 제품 수: {total_products}개")
        print(f"  제품 종류: {len(final_results)}가지")

        # 최종 결과 저장
        self.final_results = final_results
        return final_results
    
    # ==================== 결과 반환 함수들 ====================
    
    def get_current_detection_results(self):
        """현재 탐지 결과 반환"""
        if not self.tracker:
            return {
                'class_counts': {},
                'total_count': 0,
                'stable_objects': [],
                'observation_count': self.observation_count
            }
        
        class_counts, total_count = self.tracker.get_count_summary()
        return {
            'class_counts': dict(class_counts),
            'total_count': total_count,
            'stable_objects': self.tracker.stable_objects,
            'observation_count': self.observation_count
        }
    
    def get_final_results(self):
        """관찰 완료 후 최종 결과 반환"""
        if self.final_results is None:
            return {
                'final_counts': {},
                'total_products': 0,
                'product_types': 0,
                'is_complete': False,
                'observation_results': self.observation_results
            }
        
        total_products = sum(item['count'] for item in self.final_results.values())
        
        return {
            'final_counts': {class_name: info['count'] for class_name, info in self.final_results.items()},
            'total_products': total_products,
            'product_types': len(self.final_results),
            'is_complete': True,
            'observation_results': self.observation_results,
            'detailed_results': self.final_results
        }
    
    def get_count_summary(self):
        """간단한 개수 요약 반환"""
        if self.final_results:
            # 관찰 완료된 경우
            return {class_name: info['count'] for class_name, info in self.final_results.items()}
        elif self.tracker:
            # 진행 중인 경우
            class_counts, _ = self.tracker.get_count_summary()
            return dict(class_counts)
        else:
            return {}
    
    def is_detection_complete(self):
        """탐지 완료 여부 반환"""
        return self.observation_count >= self.max_observations and self.final_results is not None
        
    def is_observation_complete(self):
        """관찰 완료 여부 확인"""
        return self.observation_count >= self.max_observations
        
    def run(self):
        """메인 실행 함수 (터미널 전용)"""
        print("🍪 Level 2 Multi-frame Voting 관찰 시스템 (터미널 모드)")
        print(f"🎯 총 {self.max_observations}회 관찰 후 빈도 기반 최종 판정")
        print("=" * 60)
        
        # 초기화
        self.initialize_model()
        actual_width, actual_height = self.initialize_camera()
        self.initialize_tracker()
        
        print(f"\n🎯 {self.max_observations}회 관찰 시작!")
        print(f"  detection 간격: 매 {CAMERA_CONFIG['detection_interval']}프레임")
        print(f"  종료: {self.max_observations}회 관찰 완료 또는 Ctrl+C")
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
                    # 관찰 완료 체크
                    if self.is_observation_complete():
                        print(f"\n🎉 {self.max_observations}회 관찰 완료! 최종 분석을 시작합니다.")
                        break
                    
                    print(f"\n🔍 탐지 실행... (프레임 {self.frame_count})")
                    current_detections = self.detect_objects(frame)
                    
                    # 추적기 업데이트 (Level 2 Multi-frame Voting)
                    stable_objects = self.tracker.update(current_detections)
                    
                    # 관찰 카운트 증가
                    self.observation_count += 1
                    
                    # 터미널 출력
                    self.print_detection_summary(stable_objects)
                    
                    # 관찰 진행상황 출력
                    self.print_observation_progress()
                    
                    # 관찰 결과 기록
                    self.record_observation_result()
                
                # 자동 통계 출력
                if self.frame_count % SIMPLE_CONFIG['auto_stats_interval'] == 0:
                    class_counts, total_count = self.tracker.get_count_summary()
                    print(f"\n📊 자동 통계 (프레임 {self.frame_count}):")
                    print(f"  FPS: {current_fps:.1f}, 관찰: {self.observation_count}/{self.max_observations}")
                    print(f"  현재 총 객체: {total_count}개")
                
                # 진행상황 주기적 출력
                if self.frame_count % REPORT_CONFIG['progress_report_interval'] == 0:
                    print(f"\n📈 진행상황: 프레임 {self.frame_count}, FPS {current_fps:.1f}, 관찰 {self.observation_count}/{self.max_observations}")
                
                # CPU 부하 감소를 위한 짧은 대기
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n🔚 Ctrl+C로 종료 요청됨")
        
        # 최종 분석 수행
        if self.observation_results:
            self.analyze_final_results()
            print_final_report(self.observation_results)
        
        # 정리
        self.cap.release()
        print("🔚 Level 2 객체 개수 파악 시스템 종료")

# ==================== 전역 함수들 ====================

# 전역 detector 인스턴스
_global_detector = None

def detect_start(model_path=MODEL_PATH):
    """웹캠 객체 탐지 시작 - 터미널 모드"""
    global _global_detector
    print("🚀 웹캠 객체 탐지 시스템 시작 (터미널 모드)...")
    _global_detector = SnackDetector(model_path=model_path)
    _global_detector.run()
    return _global_detector

def detect_stop():
    """웹캠 객체 탐지 중지"""
    print("⏹️ 프로그램 종료를 위해서는 Ctrl+C를 사용하세요")

def get_detection_results():
    """현재 탐지 결과 반환 (전역 함수)"""
    global _global_detector
    if _global_detector is None:
        return {
            'error': '탐지기가 초기화되지 않았습니다. detect_start()를 먼저 실행하세요.',
            'class_counts': {},
            'total_count': 0
        }
    return _global_detector.get_current_detection_results()

def get_final_results():
    """최종 결과 반환 (전역 함수)"""
    global _global_detector
    if _global_detector is None:
        return {
            'error': '탐지기가 초기화되지 않았습니다.',
            'final_counts': {},
            'is_complete': False
        }
    return _global_detector.get_final_results()

def get_count_summary():
    """개수 요약 반환 (전역 함수)"""
    global _global_detector
    if _global_detector is None:
        return {}
    return _global_detector.get_count_summary()

def is_detection_complete():
    """탐지 완료 여부 반환 (전역 함수)"""
    global _global_detector
    if _global_detector is None:
        return False
    return _global_detector.is_detection_complete()