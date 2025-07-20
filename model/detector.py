# detector.py - 메인 탐지 클래스

import cv2
import time
import numpy as np
from ultralytics import YOLO

from config import (
    MODEL_PATH, CLASS_NAMES, WEBCAM_CONFIG, 
    DETECTION_CONFIG, DISPLAY_CONFIG
)
from utils import (
    test_gui, stabilize_detections, draw_detections, 
    draw_status_info, create_error_frame, preprocess_frame, print_help
)


class SnackDetector:
    def __init__(self, model_path=None, class_names=None, test_gui_first=True):
        """스낵 탐지기 초기화"""
        self.model_path = model_path or MODEL_PATH
        self.class_names = class_names or CLASS_NAMES
        
        # GUI 테스트
        if test_gui_first:
            test_gui()
        
        # 모델 로딩
        print("🤖 모델 로딩 중...")
        self.model = YOLO(self.model_path)
        print("✅ 모델 로드 완료")
        
        # 상태 변수들
        self.conf_threshold = DETECTION_CONFIG['conf_threshold']
        self.stabilization_mode = True
        self.detection_history = []
        self.last_detections = []
        self.last_successful_frame = None
        
        # FPS 측정
        self.fps_start = time.time()
        self.fps_counter = 0
        self.current_fps = 0
        
        # 프레임 카운터
        self.frame_count = 0
        
        # 웹캠
        self.cap = None
        
    def init_webcam(self):
        """웹캠 초기화"""
        print("📹 웹캠 초기화 중...")
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, WEBCAM_CONFIG['buffer_size'])
        
        # 해상도 설정
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_CONFIG['width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_CONFIG['height'])
        
        # MJPEG 코덱 설정
        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        self.cap.set(cv2.CAP_PROP_FPS, WEBCAM_CONFIG['fps'])
        
        if not self.cap.isOpened():
            raise Exception("❌ 웹캠 열기 실패")
        
        # 실제 해상도 확인
        self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"📷 실제 해상도: {self.actual_width}x{self.actual_height}")
        
        # 워밍업
        print("🔥 웹캠 워밍업...")
        for i in range(10):
            ret, frame = self.cap.read()
            print(f"워밍업 {i+1}: {'OK' if ret else 'FAIL'}")
            time.sleep(0.2)
        
        return True
    
    def setup_display_window(self):
        """디스플레이 창 설정"""
        cv2.namedWindow(DISPLAY_CONFIG['window_name'], cv2.WINDOW_NORMAL)
        cv2.resizeWindow(DISPLAY_CONFIG['window_name'], 
                        DISPLAY_CONFIG['display_width'], 
                        DISPLAY_CONFIG['display_height'])
    
    def process_detections(self, frame):
        """탐지 수행"""
        try:
            print(f"🔍 탐지 실행... (프레임 {self.frame_count})")
            
            # 프레임 전처리
            processed_frame = preprocess_frame(frame)
            
            start_time = time.time()
            
            # 탐지 수행
            results = self.model(processed_frame, conf=self.conf_threshold, verbose=False)
            
            inference_time = time.time() - start_time
            print(f"⏱️ 추론 시간: {inference_time:.3f}초")
            
            # 결과 파싱
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
            
            # 안정화 처리
            if self.stabilization_mode:
                self.detection_history.append(current_detections)
                if len(self.detection_history) > DETECTION_CONFIG['stabilization_frames']:
                    self.detection_history.pop(0)
                
                self.last_detections = stabilize_detections(self.detection_history, self.class_names)
            else:
                self.last_detections = current_detections
                
        except Exception as e:
            print(f"⚠️ 탐지 오류: {e}")
    
    def update_fps(self):
        """FPS 업데이트"""
        self.fps_counter += 1
        if self.fps_counter >= 30:
            current_time = time.time()
            self.current_fps = 30 / (current_time - self.fps_start)
            self.fps_start = current_time
            self.fps_counter = 0
    
    def handle_keyboard_input(self, key):
        """키보드 입력 처리"""
        if key == ord('q'):
            return False  # 종료
        elif key == ord(' '):
            filename = f"detection_{self.frame_count}.jpg"
            # 현재 표시 프레임 저장하기 위해 여기서는 True만 반환
            print(f"📸 스크린샷 요청: {filename}")
            return True
        elif key == ord('s'):
            print(f"📊 상태: 프레임 {self.frame_count}, FPS {self.current_fps:.1f}, 탐지 {len(self.last_detections)}개")
        elif key == ord('+') or key == ord('='):
            self.conf_threshold = min(0.9, self.conf_threshold + 0.05)
            print(f"📈 신뢰도 증가: {self.conf_threshold:.2f}")
        elif key == ord('-'):
            self.conf_threshold = max(0.1, self.conf_threshold - 0.05)
            print(f"📉 신뢰도 감소: {self.conf_threshold:.2f}")
        elif key == ord('f'):
            self.stabilization_mode = not self.stabilization_mode
            print(f"🔄 안정화 모드: {'ON' if self.stabilization_mode else 'OFF'}")
        
        return True
    
    def run(self):
        """메인 탐지 루프 실행"""
        try:
            # 초기화
            self.init_webcam()
            self.setup_display_window()
            print_help()
            
            while True:
                ret, frame = self.cap.read()
                
                # 프레임 읽기 실패 처리
                if not ret or frame is None:
                    print(f"❌ 프레임 {self.frame_count + 1} 읽기 실패")
                    
                    if self.last_successful_frame is not None:
                        frame = self.last_successful_frame.copy()
                        cv2.putText(frame, "CAMERA ERROR - USING LAST FRAME", 
                                   (10, self.actual_height-40), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        frame = create_error_frame(self.actual_width, self.actual_height)
                else:
                    self.last_successful_frame = frame.copy()
                
                self.frame_count += 1
                self.update_fps()
                
                # 탐지 수행 (매 N프레임마다)
                if (self.frame_count % DETECTION_CONFIG['detection_interval'] == 0 and ret):
                    self.process_detections(frame)
                
                # 화면 표시용 프레임 준비
                display_frame = frame.copy()
                
                # 탐지 결과 그리기
                display_frame = draw_detections(display_frame, self.last_detections)
                
                # 상태 정보 그리기
                display_frame = draw_status_info(
                    display_frame, self.frame_count, self.current_fps, 
                    len(self.last_detections), self.conf_threshold,
                    self.stabilization_mode, ret, 
                    self.actual_width, self.actual_height
                )
                
                # 화면 업데이트
                try:
                    cv2.imshow(DISPLAY_CONFIG['window_name'], display_frame)
                except Exception as e:
                    print(f"⚠️ 화면 표시 오류: {e}")
                
                # 키 입력 처리
                key = cv2.waitKey(1) & 0xFF
                if key != 255:  # 키가 눌렸을 때
                    if not self.handle_keyboard_input(key):
                        break
                    
                    # 스크린샷 저장
                    if key == ord(' '):
                        filename = f"detection_{self.frame_count}.jpg"
                        cv2.imwrite(filename, display_frame)
                        print(f"📸 스크린샷 저장: {filename}")
                
                # 진행상황 주기적 출력
                if self.frame_count % 100 == 0:
                    print(f"📊 진행: {self.frame_count} 프레임, FPS {self.current_fps:.1f}, 신뢰도 {self.conf_threshold:.2f}")
            
        except Exception as e:
            print(f"❌ 실행 중 오류: {e}")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """정리 작업"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("🔚 과자 탐지 종료")
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.cleanup()