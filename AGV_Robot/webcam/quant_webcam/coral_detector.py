# detection/coral_detector.py
"""YOLOv11 EdgeTPU 기반 객체 검출기"""

import numpy as np
import cv2
import time
from pycoral.utils.edgetpu import load_edgetpu_delegate
from pycoral.utils import dataset
from pycoral.adapters import common
from pycoral.adapters import detect
import tflite_runtime.interpreter as tflite

class CoralDetector:
    def __init__(self, model_path, labels_path=None):
        """YOLOv11 EdgeTPU 검출기 초기화"""
        self.model_path = model_path
        self.labels = []
        
        # 라벨 로드
        if labels_path:
            try:
                with open(labels_path, 'r', encoding='utf-8') as f:
                    self.labels = [line.strip() for line in f.readlines()]
                print(f"📋 {len(self.labels)}개 클래스 로드됨")
            except FileNotFoundError:
                print(f"⚠️ 라벨 파일을 찾을 수 없습니다: {labels_path}")
        
        # EdgeTPU 인터프리터 초기화
        print("🤖 YOLOv11 EdgeTPU 모델 로딩 중...")
        try:
            self.interpreter = tflite.Interpreter(
                model_path=model_path,
                experimental_delegates=[load_edgetpu_delegate()]
            )
            print("✅ EdgeTPU 사용")
        except Exception as e:
            print(f"⚠️ EdgeTPU 초기화 실패, CPU 사용: {e}")
            self.interpreter = tflite.Interpreter(model_path=model_path)
        
        self.interpreter.allocate_tensors()
        
        # 입력/출력 텐서 정보
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # 모델 정보 출력
        print(f"📊 입력 개수: {len(self.input_details)}")
        print(f"📊 출력 개수: {len(self.output_details)}")
        
        for i, detail in enumerate(self.input_details):
            print(f"   입력 {i}: {detail['shape']} ({detail['dtype']})")
        
        for i, detail in enumerate(self.output_details):
            print(f"   출력 {i}: {detail['shape']} ({detail['dtype']})")
        
        # 입력 크기
        self.input_height = self.input_details[0]['shape'][1]
        self.input_width = self.input_details[0]['shape'][2]
        
        print(f"📐 모델 입력 크기: {self.input_width}x{self.input_height}")
        print("✅ YOLOv11 검출기 초기화 완료")
    
    def preprocess_image(self, frame):
        """YOLOv11용 이미지 전처리"""
        # 모델 입력 크기로 리사이즈
        resized = cv2.resize(frame, (self.input_width, self.input_height))
        
        # YOLOv11 전용 전처리
        if self.input_details[0]['dtype'] == np.float32:
            # 정규화 (0-255 -> 0-1)
            input_data = np.array(resized, dtype=np.float32) / 255.0
        elif self.input_details[0]['dtype'] == np.int8:
            # INT8 양자화 모델용 (일반적으로 -128~127 범위)
            input_data = np.array(resized, dtype=np.int8)
        else:
            # UINT8
            input_data = np.array(resized, dtype=np.uint8)
        
        # 배치 차원 추가
        input_data = np.expand_dims(input_data, axis=0)
        
        return input_data
    
    def detect(self, frame, conf_threshold=0.25):
        """YOLOv11 객체 검출 수행"""
        start_time = time.time()
        
        # 원본 프레임 크기
        orig_h, orig_w = frame.shape[:2]
        
        # 전처리
        input_data = self.preprocess_image(frame)
        
        # 추론
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        
        # YOLOv11 출력 처리
        detections = []
        
        try:
            # YOLOv11은 보통 하나의 출력 텐서를 가짐
            if len(self.output_details) == 1:
                # 단일 출력 (일반적인 YOLOv11 형태)
                output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
                detections = self._parse_yolo_output(output_data, orig_w, orig_h, conf_threshold)
            
            elif len(self.output_details) == 3:
                # 분리된 출력 (boxes, classes, scores)
                boxes = self.interpreter.get_tensor(self.output_details[0]['index'])
                classes = self.interpreter.get_tensor(self.output_details[1]['index'])  
                scores = self.interpreter.get_tensor(self.output_details[2]['index'])
                detections = self._parse_separated_output(boxes, classes, scores, orig_w, orig_h, conf_threshold)
            
            else:
                print(f"⚠️ 지원하지 않는 출력 개수: {len(self.output_details)}")
                
        except Exception as e:
            print(f"⚠️ YOLOv11 출력 파싱 오류: {e}")
            # 디버깅을 위한 출력 형태 정보
            try:
                for i, detail in enumerate(self.output_details):
                    output = self.interpreter.get_tensor(detail['index'])
                    print(f"   출력 {i} 실제 형태: {output.shape}")
            except:
                pass
        
        inference_time = time.time() - start_time
        return detections, inference_time
    
    def _parse_yolo_output(self, output_data, orig_w, orig_h, conf_threshold):
        """YOLOv11 단일 출력 파싱"""
        detections = []
        
        # YOLOv11 출력은 보통 [1, num_detections, 4+1+num_classes] 형태
        # 또는 [1, num_detections, 4+num_classes] 형태 (objectness 없이)
        
        if len(output_data.shape) == 3:
            predictions = output_data[0]  # 배치 차원 제거
        else:
            predictions = output_data
        
        for pred in predictions:
            if len(pred) >= 5:  # 최소 bbox(4) + conf(1)
                # YOLOv11 형태: [x_center, y_center, width, height, conf, class_scores...]
                x_center, y_center, width, height = pred[:4]
                objectness = pred[4] if len(pred) > 5 else 1.0
                
                # 클래스 점수들
                if len(pred) > 5:
                    class_scores = pred[5:]
                    class_id = np.argmax(class_scores)
                    class_conf = class_scores[class_id]
                    total_conf = objectness * class_conf
                else:
                    class_id = 0
                    total_conf = objectness
                
                if total_conf >= conf_threshold:
                    # YOLO 좌표를 픽셀 좌표로 변환
                    x1 = int((x_center - width/2) * orig_w)
                    y1 = int((y_center - height/2) * orig_h)
                    x2 = int((x_center + width/2) * orig_w)
                    y2 = int((y_center + height/2) * orig_h)
                    
                    # 경계 검사
                    x1 = max(0, min(x1, orig_w))
                    y1 = max(0, min(y1, orig_h))
                    x2 = max(0, min(x2, orig_w))
                    y2 = max(0, min(y2, orig_h))
                    
                    # 클래스명
                    if class_id < len(self.labels):
                        class_name = self.labels[class_id]
                    else:
                        class_name = f"Class_{class_id}"
                    
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'name': class_name,
                        'confidence': float(total_conf)
                    })
        
        return detections
    
    def _parse_separated_output(self, boxes, classes, scores, orig_w, orig_h, conf_threshold):
        """분리된 출력 파싱 (기존 코드와 유사)"""
        detections = []
        
        # 배치 차원이 있다면 제거
        if len(boxes.shape) > 2:
            boxes = boxes[0]
        if len(classes.shape) > 1:
            classes = classes[0]
        if len(scores.shape) > 1:
            scores = scores[0]
        
        for i in range(len(scores)):
            if scores[i] >= conf_threshold:
                # 박스 좌표
                if len(boxes[i]) == 4:
                    ymin, xmin, ymax, xmax = boxes[i]
                    x1 = int(xmin * orig_w)
                    y1 = int(ymin * orig_h)
                    x2 = int(xmax * orig_w)
                    y2 = int(ymax * orig_h)
                else:
                    continue
                
                class_id = int(classes[i])
                confidence = float(scores[i])
                
                # 클래스명
                if class_id < len(self.labels):
                    class_name = self.labels[class_id]
                else:
                    class_name = f"Class_{class_id}"
                
                detections.append({
                    'bbox': (x1, y1, x2, y2),
                    'name': class_name,
                    'confidence': confidence
                })
        
        return detections
    
    def get_model_info(self):
        """모델 정보 반환"""
        return {
            'input_shape': (self.input_width, self.input_height),
            'num_labels': len(self.labels),
            'labels': self.labels,
            'num_outputs': len(self.output_details)
        }