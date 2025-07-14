import cv2
import numpy as np
from openvino.runtime import Core, get_version
import time
import argparse
import os

class YOLOOpenVINO:
    def __init__(self, model_path, device='CPU', conf_threshold=0.5, nms_threshold=0.4):
        """
        YOLO OpenVINO 모델 초기화
        
        Args:
            model_path: .xml 파일 경로
            device: 추론 장치 ('CPU', 'GPU', 'MYRIAD' 등)
            conf_threshold: 신뢰도 임계값
            nms_threshold: NMS 임계값
        """
        self.core = Core()
        self.device = device
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        
        # 과자 클래스 이름 (실제 모델에 맞게 수정)
        self.class_names = [
            "crown_BigPie_Strawberry", "crown_ChocoHaim", "crown_Concho",
            "crown_Potto_Cheese_Tart", "haetae_Guun_Gamja", "haetae_HoneyButterChip",
            "haetae_Masdongsan", "haetae_Osajjeu", "haetae_Oyeseu", "lotte_kkokkalkon_gosohanmas",
            "nongshim_Alsaeuchip", "nongshim_Banana_Kick", "nongshim_ChipPotato_Original",
            "nongshim_Ojingeojip", "orion_Chocolate_Chip_Cookies", "orion_Diget_Choco",
            "orion_Diget_tongmil","orion_Fresh_Berry", "orion_Gosomi", "orion_Pocachip_Original",
            "orion_chokchokhan_Chocochip"
                            ]
        
        # 모델 로드
        print(f"OpenVINO 버전: {get_version()}")
        print(f"YOLO 모델 로드 중: {model_path}")
        
        self.model = self.core.read_model(model_path)
        self.compiled_model = self.core.compile_model(self.model, device)
        
        # 입력/출력 정보 가져오기
        self.input_layer = self.compiled_model.input(0)
        self.output_layer = self.compiled_model.output(0)
        
        # 입력 형태 정보
        self.input_shape = self.input_layer.shape
        self.input_height = self.input_shape[2]
        self.input_width = self.input_shape[3]
        
        print(f"입력 형태: {self.input_shape}")
        print(f"출력 형태: {self.output_layer.shape}")
        print(f"사용 장치: {device}")
        
        # 추론 요청 생성
        self.infer_request = self.compiled_model.create_infer_request()
        
    def preprocess_frame(self, frame):
        """
        YOLO 전처리: 비율 유지하며 리사이즈 + 패딩
        """
        # 원본 프레임 크기
        original_height, original_width = frame.shape[:2]
        
        # 비율 계산
        ratio = min(self.input_width / original_width, self.input_height / original_height)
        
        # 새로운 크기 계산
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        # 리사이즈
        resized_frame = cv2.resize(frame, (new_width, new_height))
        
        # 패딩을 위한 캔버스 생성
        padded_frame = np.full((self.input_height, self.input_width, 3), 114, dtype=np.uint8)
        
        # 중앙에 이미지 배치
        start_x = (self.input_width - new_width) // 2
        start_y = (self.input_height - new_height) // 2
        padded_frame[start_y:start_y + new_height, start_x:start_x + new_width] = resized_frame
        
        # 정규화 (0-255 -> 0-1)
        normalized_frame = padded_frame.astype(np.float32) / 255.0
        
        # 차원 변경 (H, W, C) -> (1, C, H, W)
        input_tensor = np.transpose(normalized_frame, (2, 0, 1))
        input_tensor = np.expand_dims(input_tensor, axis=0)
        
        return input_tensor, ratio, start_x, start_y
    
    def postprocess_yolo(self, output, original_frame, ratio, pad_x, pad_y):
        """
        YOLO 출력 후처리
        """
        # 원본 프레임 크기
        original_height, original_width = original_frame.shape[:2]
        
        # 출력 형태 처리
        if len(output.shape) == 3:
            output = output[0]  # 배치 차원 제거
        
        # 출력이 (num_boxes, 85) 형태라고 가정 (4 + 1 + 80 classes)
        # 또는 (num_boxes, num_classes + 5) 형태
        
        boxes = []
        confidences = []
        class_ids = []
        
        # 각 검출 결과 처리
        for detection in output:
            # 신뢰도 점수들 (클래스별)
            scores = detection[5:]  # 첫 5개는 x, y, w, h, objectness
            class_id = np.argmax(scores)
            confidence = scores[class_id] * detection[4]  # class_confidence * objectness
            
            if confidence > self.conf_threshold:
                # 박스 좌표 (중심점 + 너비/높이)
                center_x = detection[0]
                center_y = detection[1]
                width = detection[2]
                height = detection[3]
                
                # 좌상단 좌표로 변환
                x1 = center_x - width / 2
                y1 = center_y - height / 2
                
                # 패딩 보정
                x1 = (x1 - pad_x) / ratio
                y1 = (y1 - pad_y) / ratio
                width = width / ratio
                height = height / ratio
                
                # 원본 이미지 크기로 스케일링
                x1 = max(0, min(x1, original_width))
                y1 = max(0, min(y1, original_height))
                x2 = max(0, min(x1 + width, original_width))
                y2 = max(0, min(y1 + height, original_height))
                
                boxes.append([int(x1), int(y1), int(x2), int(y2)])
                confidences.append(float(confidence))
                class_ids.append(class_id)
        
        # NMS 적용
        if len(boxes) > 0:
            # OpenCV NMS 형식으로 변환
            nms_boxes = [[box[0], box[1], box[2] - box[0], box[3] - box[1]] for box in boxes]
            indices = cv2.dnn.NMSBoxes(nms_boxes, confidences, self.conf_threshold, self.nms_threshold)
            
            final_boxes = []
            final_confidences = []
            final_class_ids = []
            
            if len(indices) > 0:
                for i in indices.flatten():
                    final_boxes.append(boxes[i])
                    final_confidences.append(confidences[i])
                    final_class_ids.append(class_ids[i])
            
            return final_boxes, final_confidences, final_class_ids
        
        return [], [], []
    
    def draw_detections(self, frame, boxes, confidences, class_ids):
        """
        검출 결과를 프레임에 그리기
        """
        colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), 
                  (0, 255, 255), (128, 0, 128), (255, 165, 0), (255, 192, 203), (0, 128, 0)]
        
        detection_info = []
        
        for i, (box, confidence, class_id) in enumerate(zip(boxes, confidences, class_ids)):
            x1, y1, x2, y2 = box
            
            # 클래스 이름 가져오기
            class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"Class_{class_id}"
            
            # 색상 선택
            color = colors[class_id % len(colors)]
            
            # 바운딩 박스 그리기
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # 라벨 텍스트
            label = f"{class_name}: {confidence:.2f}"
            
            # 텍스트 배경
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(frame, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
            
            # 텍스트 그리기
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            detection_info.append(f"{class_name}: {confidence:.2f}")
        
        return frame, detection_info
    
    def infer(self, frame):
        """
        추론 수행
        """
        # 전처리
        input_tensor, ratio, pad_x, pad_y = self.preprocess_frame(frame)
        
        # 추론
        start_time = time.time()
        results = self.infer_request.infer({self.input_layer: input_tensor})
        inference_time = time.time() - start_time
        
        # 결과 추출
        output_data = results[self.output_layer]
        
        # 후처리
        boxes, confidences, class_ids = self.postprocess_yolo(output_data, frame, ratio, pad_x, pad_y)
        
        # 검출 결과 그리기
        result_frame, detection_info = self.draw_detections(frame.copy(), boxes, confidences, class_ids)
        
        return result_frame, detection_info, inference_time

def main():
    parser = argparse.ArgumentParser(description="YOLO 과자 탐지 카메라 테스트")
    parser.add_argument("--model", default="model/best.xml", help="모델 경로 (.xml 파일)")
    parser.add_argument("--device", default="CPU", help="추론 장치 (CPU, GPU, MYRIAD)")
    parser.add_argument("--conf", type=float, default=0.5, help="신뢰도 임계값")
    parser.add_argument("--nms", type=float, default=0.4, help="NMS 임계값")
    parser.add_argument("--camera", type=int, default=0, help="카메라 인덱스")
    
    args = parser.parse_args()
    
    # 모델 파일 존재 확인
    if not os.path.exists(args.model):
        print(f"모델 파일을 찾을 수 없습니다: {args.model}")
        return
    
    # YOLO 모델 초기화
    try:
        yolo = YOLOOpenVINO(args.model, args.device, args.conf, args.nms)
    except Exception as e:
        print(f"모델 로드 실패: {e}")
        return
    
    # 카메라 초기화
    cap = cv2.VideoCapture(args.camera)
    
    # 카메라 설정
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return
    
    print("카메라 테스트 시작...")
    print("종료하려면 'q' 키를 누르세요.")
    
    # FPS 계산을 위한 변수
    fps_counter = 0
    fps_start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("프레임을 읽을 수 없습니다.")
                break
            
            # 추론 수행
            result_frame, detections, inference_time = yolo.infer(frame)
            
            # FPS 계산
            fps_counter += 1
            if fps_counter % 30 == 0:  # 30프레임마다 FPS 계산
                fps_end_time = time.time()
                fps = 30 / (fps_end_time - fps_start_time)
                fps_start_time = fps_end_time
                print(f"FPS: {fps:.2f}")
            
            # 정보 표시
            info_text = f"추론 시간: {inference_time*1000:.1f}ms | 검출: {len(detections)}개"
            cv2.putText(result_frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 검출된 과자 정보 출력
            if detections:
                y_offset = 60
                for detection in detections:
                    cv2.putText(result_frame, detection, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    y_offset += 25
            
            # 결과 표시
            cv2.imshow('YOLO 과자 탐지', result_frame)
            
            # 콘솔에 검출 정보 출력
            if detections:
                print(f"검출된 과자: {detections}")
            
            # 'q' 키로 종료
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("카메라 테스트 완료")

if __name__ == "__main__":
    main()