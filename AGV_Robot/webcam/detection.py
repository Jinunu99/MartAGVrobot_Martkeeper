import cv2
import time
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
        print("✅ 모델 로드 완료")
        
    def initialize_camera(self):
        """카메라 초기화"""
        print("📹 웹캠 초기화 중...")
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_CONFIG['buffer_size'])
        
        # USB 2.0에 최적화된 해상도
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
            print(f"워밍업 {i+1}: {'OK' if ret else 'FAIL'}")
            time.sleep(0.2)
            
        return actual_width, actual_height
        
    def initialize_tracker(self):
        """추적기 초기화"""
        self.tracker = ObjectTracker(**TRACKER_CONFIG)
        
    def gui_test(self):
        """GUI 기본 테스트"""
        print("🧪 GUI 기본 테스트...")
        test_img = np.zeros((200, 400, 3), dtype=np.uint8)
        test_img[50:150, 50:350] = [0, 255, 0]
        cv2.putText(test_img, "GUI Working!", (100, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        cv2.namedWindow('GUI Test', cv2.WINDOW_NORMAL)
        cv2.imshow('GUI Test', test_img)
        print("GUI 테스트 창이 보이나요? 2초 후 자동으로 닫힙니다.")
        cv2.waitKey(UI_CONFIG['gui_test_duration'])
        cv2.destroyAllWindows()
        
    def detect_objects(self, frame):
        """프레임에서 객체 탐지"""
        try:
            # 프레임 전처리
            processed_frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=5)
            
            start_time = time.time()
            
            # YOLO 탐지
            results = self.model(processed_frame, conf=self.conf_threshold, verbose=False)
            
            inference_time = time.time() - start_time
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
                        
                        print(f"🎯 탐지: {class_name} ({confidence:.2f})")
            
            return current_detections
            
        except Exception as e:
            print(f"⚠️ 탐지 오류: {e}")
            return []
            
    def draw_objects(self, frame, stable_objects, actual_width, actual_height, current_fps):
        """프레임에 탐지된 객체들 그리기"""
        display_frame = frame.copy()
        
        # 안정화된 객체들 그리기
        for obj in stable_objects:
            x1, y1, x2, y2 = obj['bbox']
            class_name = obj['name']
            confidence = obj['confidence']
            votes = obj['votes']
            stability = obj['stability']
            
            # 안정성에 따른 색상 변경
            if stability > STABILITY_THRESHOLDS['very_stable']:
                color = COLORS['very_stable']    # 매우 안정: 초록색
            elif stability > STABILITY_THRESHOLDS['stable']:
                color = COLORS['stable']         # 안정: 노란색
            elif stability > STABILITY_THRESHOLDS['moderate']:
                color = COLORS['moderate']       # 보통: 주황색
            else:
                color = COLORS['unstable']       # 불안정: 보라색
            
            # 바운딩 박스 (두께는 안정성에 비례)
            thickness = max(1, int(stability * 4))
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, thickness)
            
            # 라벨 (투표 수와 안정성 포함)
            label = f"{class_name}"
            confidence_label = f"Conf:{confidence:.2f}"
            stability_label = f"Votes:{votes}/Stab:{stability:.2f}"
            
            cv2.putText(display_frame, label, (x1, y1-30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(display_frame, confidence_label, (x1, y1-15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            cv2.putText(display_frame, stability_label, (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # 현재 개수 통계 표시
        class_counts, total_count = self.tracker.get_count_summary()
        
        # 상태 정보 표시 (왼쪽)
        cv2.putText(display_frame, f"Frame: {self.frame_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, UI_CONFIG['font_scale'], COLORS['text'], UI_CONFIG['font_thickness'])
        cv2.putText(display_frame, f"FPS: {current_fps:.1f}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, UI_CONFIG['font_scale'], COLORS['text'], UI_CONFIG['font_thickness'])
        cv2.putText(display_frame, f"Total Objects: {total_count}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, UI_CONFIG['font_scale'], COLORS['count_text'], UI_CONFIG['font_thickness'])
        cv2.putText(display_frame, f"Conf Threshold: {self.conf_threshold:.2f}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, UI_CONFIG['font_scale'], COLORS['text'], UI_CONFIG['font_thickness'])
        
        # 클래스별 개수 표시 (오른쪽)
        y_offset = 30
        cv2.putText(display_frame, "Class Counts:", (actual_width-200, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLORS['class_text'], 2)
        
        for class_name, count in class_counts.items():
            if count > 0:
                y_offset += 25
                short_name = class_name.split('_')[0] if '_' in class_name else class_name[:10]
                cv2.putText(display_frame, f"{short_name}: {count}", 
                           (actual_width-200, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['text'], 1)
        
        return display_frame
        
    def handle_key_input(self, key, display_frame):
        """키 입력 처리"""
        if key == KEY_MAPPINGS['quit']:
            return False
        elif key == KEY_MAPPINGS['screenshot']:
            filename = f"level2_detection_{self.frame_count}.jpg"
            cv2.imwrite(filename, display_frame)
            print(f"📸 스크린샷 저장: {filename}")
        elif key == KEY_MAPPINGS['statistics']:
            class_counts, total_count = self.tracker.get_count_summary()
            print(f"📊 현재 상태:")
            print(f"  프레임: {self.frame_count}, 총 객체: {total_count}")
            print(f"  클래스별: {dict(class_counts)}")
        elif key in KEY_MAPPINGS['increase_conf']:
            self.conf_threshold = min(CONFIDENCE_CONFIG['max_threshold'], 
                                    self.conf_threshold + CONFIDENCE_CONFIG['adjustment_step'])
            print(f"📈 신뢰도 증가: {self.conf_threshold:.2f}")
        elif key == KEY_MAPPINGS['decrease_conf']:
            self.conf_threshold = max(CONFIDENCE_CONFIG['min_threshold'], 
                                    self.conf_threshold - CONFIDENCE_CONFIG['adjustment_step'])
            print(f"📉 신뢰도 감소: {self.conf_threshold:.2f}")
        elif key == KEY_MAPPINGS['reset_tracker']:
            self.initialize_tracker()
            print("🔄 추적기 리셋 완료")
        elif key == KEY_MAPPINGS['count_report']:
            class_counts, total_count = self.tracker.get_count_summary()
            print_count_report(self.count_history, class_counts, total_count)
        
        return True
        
    def run(self):
        """메인 실행 함수"""
        print("🍪 Level 2 Multi-frame Voting 객체 개수 파악 시스템")
        
        # 초기화
        self.gui_test()
        self.initialize_model()
        actual_width, actual_height = self.initialize_camera()
        self.initialize_tracker()
        
        # OpenCV 창 미리 생성 및 설정
        window_name = UI_CONFIG['window_name']
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, UI_CONFIG['window_width'], UI_CONFIG['window_height'])
        
        print("🎯 Level 2 객체 개수 파악 시작!")
        print("주요 조작:")
        print("  'q': 종료")
        print("  'SPACE': 스크린샷")
        print("  's': 통계 출력")
        print("  '+/-': 신뢰도 조절")
        print("  'r': 추적기 리셋")
        print("  'c': 개수 카운팅 보고서")
        
        last_successful_frame = None
        
        # FPS 측정
        fps_start = time.time()
        fps_counter = 0
        current_fps = 0
        
        while True:
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                print(f"❌ 프레임 {self.frame_count + 1} 읽기 실패")
                
                if last_successful_frame is not None:
                    frame = last_successful_frame.copy()
                    cv2.putText(frame, "CAMERA ERROR - USING LAST FRAME", (10, actual_height-40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    frame = np.zeros((actual_height, actual_width, 3), dtype=np.uint8)
                    cv2.putText(frame, "CAMERA ERROR", (actual_width//2-100, actual_height//2), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            else:
                last_successful_frame = frame.copy()
            
            self.frame_count += 1
            fps_counter += 1
             
            # FPS 계산
            if fps_counter >= FPS_CONFIG['measurement_interval']:
                current_time = time.time()
                current_fps = FPS_CONFIG['measurement_interval'] / (current_time - fps_start)
                fps_start = current_time
                fps_counter = 0
            
            # 탐지는 설정된 간격마다
            if self.frame_count % CAMERA_CONFIG['detection_interval'] == 0 and ret:
                print(f"🔍 탐지 실행... (프레임 {self.frame_count})")
                current_detections = self.detect_objects(frame)
                
                # 추적기 업데이트 (Level 2 Multi-frame Voting)
                stable_objects = self.tracker.update(current_detections)
                
                # 개수 통계 기록
                class_counts, total_count = self.tracker.get_count_summary()
                self.count_history.append({
                    'frame': self.frame_count,
                    'total': total_count,
                    'classes': dict(class_counts)
                })
            else:
                stable_objects = self.tracker.stable_objects
            
            # 화면 표시
            display_frame = self.draw_objects(frame, stable_objects, actual_width, actual_height, current_fps)
            
            # 카메라 상태 표시
            status_color = (0, 255, 0) if ret else (0, 0, 255)
            status_text = "CAM OK" if ret else "CAM ERROR"
            cv2.putText(display_frame, status_text, (actual_width-150, actual_height-20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            # 화면 업데이트
            try:
                cv2.imshow(window_name, display_frame)
            except Exception as e:
                print(f"⚠️ 화면 표시 오류: {e}")
            
            # 키 입력 처리
            key = cv2.waitKey(1) & 0xFF
            if not self.handle_key_input(key, display_frame):
                break
            
            # 진행상황 주기적 출력
            if self.frame_count % REPORT_CONFIG['progress_report_interval'] == 0:
                class_counts, total_count = self.tracker.get_count_summary()
                print(f"📊 진행: {self.frame_count} 프레임, FPS {current_fps:.1f}, 총 객체 {total_count}개")
        
        # 정리
        self.cap.release()
        cv2.destroyAllWindows()
        print("🔚 Level 2 객체 개수 파악 시스템 종료")

# 간단한 실행 함수
def detect_start(model_path=MODEL_PATH):
    """웹캠 객체 탐지 시작 - 다른 시스템에서 호출용"""
    print("🚀 웹캠 객체 탐지 시스템 시작...")
    detector = SnackDetector(model_path=model_path)
    detector.run()

def detect_stop():
    """웹캠 객체 탐지 중지 - 향후 확장용"""
    print("⏹️ 웹캠 객체 탐지 시스템 중지...")
    cv2.destroyAllWindows()