""" 테스트용 .pt 확장자에서만 동작함 """

import cv2
import time
from ultralytics import YOLO
import numpy as np
from collections import defaultdict, deque

def calculate_iou(box1, box2):
    """두 바운딩 박스의 IoU 계산"""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # 교집합 영역 계산
    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)
    
    if x2_inter <= x1_inter or y2_inter <= y1_inter:
        return 0.0
    
    # 교집합 넓이
    inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
    
    # 각 박스의 넓이
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    
    # 합집합 넓이
    union_area = box1_area + box2_area - inter_area
    
    return inter_area / union_area if union_area > 0 else 0.0

def calculate_distance(box1, box2):
    """두 바운딩 박스 중심점 간의 거리 계산"""
    x1_center = (box1[0] + box1[2]) / 2
    y1_center = (box1[1] + box1[3]) / 2
    x2_center = (box2[0] + box2[2]) / 2
    y2_center = (box2[1] + box2[3]) / 2
    
    return np.sqrt((x1_center - x2_center)**2 + (y1_center - y2_center)**2)

class ObjectTracker:
    """Level 2 Multi-frame Voting 기반 객체 추적기"""
    
    def __init__(self, max_history=15, min_votes=8, iou_threshold=0.3, distance_threshold=50):
        self.max_history = max_history  # 최대 히스토리 프레임 수
        self.min_votes = min_votes      # 최소 투표 수 (유효 객체 판정)
        self.iou_threshold = iou_threshold      # IoU 임계값 (같은 객체 판정)
        self.distance_threshold = distance_threshold  # 거리 임계값
        
        # 탐지 히스토리 저장
        self.detection_history = deque(maxlen=max_history)
        
        # 안정화된 객체들
        self.stable_objects = []
        
        # 통계 정보
        self.class_counts = defaultdict(int)
        self.total_objects = 0
        
    def update(self, current_detections):
        """새로운 프레임의 탐지 결과로 업데이트"""
        # 현재 탐지 결과를 히스토리에 추가
        self.detection_history.append(current_detections)
        
        # Multi-frame Voting 수행
        self.stable_objects = self._perform_voting()
        
        # 개수 통계 업데이트
        self._update_statistics()
        
        return self.stable_objects
    
    def _perform_voting(self):
        """Multi-frame Voting 알고리즘 수행"""
        if len(self.detection_history) < 3:  # 최소 3프레임 필요
            return []
        
        # 1단계: 모든 탐지 결과를 클래스별로 그룹화
        class_groups = defaultdict(list)
        
        for frame_idx, detections in enumerate(self.detection_history):
            for detection in detections:
                class_name = detection['name']
                class_groups[class_name].append({
                    'detection': detection,
                    'frame_idx': frame_idx,
                    'timestamp': len(self.detection_history) - frame_idx  # 최신도
                })
        
        stable_objects = []
        
        # 2단계: 클래스별로 공간적 클러스터링 및 투표
        for class_name, detections in class_groups.items():
            if len(detections) < 3:  # 너무 적은 탐지는 제외
                continue
            
            # 공간적 클러스터링
            clusters = self._spatial_clustering(detections)
            
            # 각 클러스터에 대해 투표 수행
            for cluster in clusters:
                votes = len(cluster)
                if votes >= self.min_votes:
                    # 클러스터의 대표 객체 생성
                    representative = self._create_representative(cluster)
                    if representative:
                        stable_objects.append(representative)
        
        return stable_objects
    
    def _spatial_clustering(self, detections):
        """공간적 클러스터링 수행"""
        clusters = []
        used_indices = set()
        
        for i, detection1 in enumerate(detections):
            if i in used_indices:
                continue
            
            # 새 클러스터 시작
            cluster = [detection1]
            used_indices.add(i)
            
            bbox1 = detection1['detection']['bbox']
            
            # 비슷한 위치의 다른 탐지들 찾기
            for j, detection2 in enumerate(detections):
                if j in used_indices:
                    continue
                
                bbox2 = detection2['detection']['bbox']
                
                # IoU 또는 거리 기준으로 같은 객체 판정
                iou = calculate_iou(bbox1, bbox2)
                distance = calculate_distance(bbox1, bbox2)
                
                if iou > self.iou_threshold or distance < self.distance_threshold:
                    cluster.append(detection2)
                    used_indices.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def _create_representative(self, cluster):
        """클러스터의 대표 객체 생성"""
        if not cluster:
            return None
        
        # 가중 평균으로 위치 계산 (최신 프레임에 더 높은 가중치)
        total_weight = 0
        weighted_x1, weighted_y1, weighted_x2, weighted_y2 = 0, 0, 0, 0
        max_confidence = 0
        class_name = cluster[0]['detection']['name']
        
        for item in cluster:
            detection = item['detection']
            weight = item['timestamp']  # 최신도를 가중치로 사용
            bbox = detection['bbox']
            confidence = detection['confidence']
            
            weighted_x1 += bbox[0] * weight
            weighted_y1 += bbox[1] * weight
            weighted_x2 += bbox[2] * weight
            weighted_y2 += bbox[3] * weight
            total_weight += weight
            
            max_confidence = max(max_confidence, confidence)
        
        if total_weight == 0:
            return None
        
        # 평균 위치 계산
        avg_bbox = (
            int(weighted_x1 / total_weight),
            int(weighted_y1 / total_weight),
            int(weighted_x2 / total_weight),
            int(weighted_y2 / total_weight)
        )
        
        # 투표 수 계산 (신뢰도 반영)
        vote_score = len(cluster) / self.max_history
        stability_score = min(1.0, len(cluster) / self.min_votes)
        
        return {
            'bbox': avg_bbox,
            'name': class_name,
            'confidence': max_confidence,
            'votes': len(cluster),
            'vote_score': vote_score,
            'stability': stability_score
        }
    
    def _update_statistics(self):
        """통계 정보 업데이트"""
        self.class_counts = defaultdict(int)
        
        for obj in self.stable_objects:
            self.class_counts[obj['name']] += 1
        
        self.total_objects = len(self.stable_objects)
    
    def get_count_summary(self):
        """클래스별 개수 요약 반환"""
        return dict(self.class_counts), self.total_objects

def improved_webcam_detection():
    """Level 2 Multi-frame Voting 기반 웹캠 탐지"""
    print("🍪 Level 2 Multi-frame Voting 객체 개수 파악 시스템")
    
    # 먼저 GUI 테스트
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
    
    # 모델 로딩
    model_path = "/home/paper/workspace/MartAGVrobot_Martkeeper/model/best.pt"
    print("🤖 모델 로딩 중...")
    model = YOLO(model_path)
    print("✅ 모델 로드 완료")
    
    # 클래스명
    class_names = ['crown_BigPie_Strawberry_324G', 'crown_ChocoHaim_142G', 'crown_Concho_66G',
                   'crown_Potto_Cheese_Tart_322G', 'haetae_Guun_Gamja_162G', 'haetae_HoneyButterChip_38G',
                   'haetae_Masdongsan_90G', 'haetae_Osajjeu_60G', 'haetae_Oyeseu_360G',
                   'lotte_kkokkalkon_gosohanmas_72G', 'nongshim_Alsaeuchip_68G', 'nongshim_Banana_Kick_75G',
                   'nongshim_ChipPotato_Original_125G', 'nongshim_Ojingeojip_83G' ,'orion_Chocolate_Chip_Cookies_256G',
                   'orion_Diget_Choco_312G', 'orion_Diget_tongmil_28_194G', 'orion_Fresh_Berry_336G',
                   'orion_Gosomi_80G', 'orion_Pocachip_Original_66G', 'orion_chokchokhan_Chocochip_240G'
                   ]
    
    # 객체 추적기 초기화
    tracker = ObjectTracker(
        max_history=15,    # 15프레임 히스토리
        min_votes=8,       # 최소 8프레임에서 탐지되어야 유효
        iou_threshold=0.3, # IoU 30% 이상이면 같은 객체
        distance_threshold=50  # 거리 50픽셀 이내면 같은 객체
    )
    
    # 웹캠 초기화
    print("📹 웹캠 초기화 중...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # USB 2.0에 최적화된 해상도
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    
    # MJPEG 코덱으로 압축 효율 향상
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FPS, 10)
    
    if not cap.isOpened():
        print("❌ 웹캠 열기 실패")
        return
    
    # 실제 해상도 확인
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"📷 실제 해상도: {actual_width}x{actual_height}")
    
    # 워밍업
    print("🔥 웹캠 워밍업...")
    for i in range(10):
        ret, frame = cap.read()
        print(f"워밍업 {i+1}: {'OK' if ret else 'FAIL'}")
        time.sleep(0.2)
    
    # OpenCV 창 미리 생성 및 설정
    window_name = 'Level 2 Object Counting System'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)
    
    print("🎯 Level 2 객체 개수 파악 시작!")
    print("주요 조작:")
    print("  'q': 종료")
    print("  'SPACE': 스크린샷")
    print("  's': 통계 출력")
    print("  '+/-': 신뢰도 조절")
    print("  'r': 추적기 리셋")
    print("  'c': 개수 카운팅 보고서")
    
    frame_count = 0
    conf_threshold = 0.25
    last_successful_frame = None
    
    # FPS 측정
    fps_start = time.time()
    fps_counter = 0
    current_fps = 0
    
    # 개수 보고서 변수
    count_history = deque(maxlen=100)  # 최근 100프레임의 개수 기록
    
    while True:
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print(f"❌ 프레임 {frame_count + 1} 읽기 실패")
            
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
        
        frame_count += 1
        fps_counter += 1
         
        # FPS 계산
        if fps_counter >= 30:
            current_time = time.time()
            current_fps = 30 / (current_time - fps_start)
            fps_start = current_time
            fps_counter = 0
        
        # 탐지는 매 3프레임마다
        if frame_count % 3 == 0 and ret:
            try:
                print(f"🔍 탐지 실행... (프레임 {frame_count})")
                
                # 프레임 전처리
                processed_frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=5)
                
                start_time = time.time()
                
                # YOLO 탐지
                results = model(processed_frame, conf=conf_threshold, verbose=False)
                
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
                            
                            if class_id < len(class_names):
                                class_name = class_names[class_id]
                            else:
                                class_name = f"Unknown_{class_id}"
                            
                            current_detections.append({
                                'bbox': (x1, y1, x2, y2),
                                'name': class_name,
                                'confidence': confidence
                            })
                            
                            print(f"🎯 탐지: {class_name} ({confidence:.2f})")
                
                # 추적기 업데이트 (Level 2 Multi-frame Voting)
                stable_objects = tracker.update(current_detections)
                
                # 개수 통계 기록
                class_counts, total_count = tracker.get_count_summary()
                count_history.append({
                    'frame': frame_count,
                    'total': total_count,
                    'classes': dict(class_counts)
                })
                
            except Exception as e:
                print(f"⚠️ 탐지 오류: {e}")
                stable_objects = []
        else:
            stable_objects = tracker.stable_objects
        
        # 화면 표시용 프레임 준비
        display_frame = frame.copy()
        
        # 안정화된 객체들 그리기
        for obj in stable_objects:
            x1, y1, x2, y2 = obj['bbox']
            class_name = obj['name']
            confidence = obj['confidence']
            votes = obj['votes']
            stability = obj['stability']
            
            # 안정성에 따른 색상 변경
            if stability > 0.8:
                color = (0, 255, 0)      # 매우 안정: 초록색
            elif stability > 0.6:
                color = (0, 255, 255)    # 안정: 노란색
            elif stability > 0.4:
                color = (0, 165, 255)    # 보통: 주황색
            else:
                color = (255, 0, 255)    # 불안정: 보라색
            
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
        class_counts, total_count = tracker.get_count_summary()
        
        # 상태 정보 표시 (왼쪽)
        cv2.putText(display_frame, f"Frame: {frame_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, f"FPS: {current_fps:.1f}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, f"Total Objects: {total_count}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, f"Conf Threshold: {conf_threshold:.2f}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 클래스별 개수 표시 (오른쪽)
        y_offset = 30
        cv2.putText(display_frame, "Class Counts:", (actual_width-200, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        for class_name, count in class_counts.items():
            if count > 0:
                y_offset += 25
                short_name = class_name.split('_')[0] if '_' in class_name else class_name[:10]
                cv2.putText(display_frame, f"{short_name}: {count}", 
                           (actual_width-200, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
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
        
        if key == ord('q'):
            print("사용자 종료 요청")
            break
        elif key == ord(' '):
            filename = f"level2_detection_{frame_count}.jpg"
            cv2.imwrite(filename, display_frame)
            print(f"📸 스크린샷 저장: {filename}")
        elif key == ord('s'):
            print(f"📊 현재 상태:")
            print(f"  프레임: {frame_count}, FPS: {current_fps:.1f}")
            print(f"  총 객체: {total_count}")
            print(f"  클래스별: {dict(class_counts)}")
        elif key == ord('+') or key == ord('='):
            conf_threshold = min(0.9, conf_threshold + 0.05)
            print(f"📈 신뢰도 증가: {conf_threshold:.2f}")
        elif key == ord('-'):
            conf_threshold = max(0.1, conf_threshold - 0.05)
            print(f"📉 신뢰도 감소: {conf_threshold:.2f}")
        elif key == ord('r'):
            tracker = ObjectTracker(max_history=15, min_votes=8, iou_threshold=0.3, distance_threshold=50)
            print("🔄 추적기 리셋 완료")
        elif key == ord('c'):
            print_count_report(count_history, class_counts, total_count)
        
        # 진행상황 주기적 출력
        if frame_count % 100 == 0:
            print(f"📊 진행: {frame_count} 프레임, FPS {current_fps:.1f}, 총 객체 {total_count}개")
    
    # 정리
    cap.release()
    cv2.destroyAllWindows()
    print("🔚 Level 2 객체 개수 파악 시스템 종료")

def print_count_report(count_history, current_counts, current_total):
    """개수 카운팅 보고서 출력"""
    print("\n" + "="*60)
    print("📊 Level 2 Multi-frame Voting 개수 파악 보고서")
    print("="*60)
    
    if not count_history:
        print("❌ 충분한 데이터가 없습니다.")
        return
    
    # 최근 데이터 분석
    recent_counts = list(count_history)[-20:]  # 최근 20프레임
    
    # 안정성 분석
    total_counts = [entry['total'] for entry in recent_counts]
    if total_counts:
        avg_total = sum(total_counts) / len(total_counts)
        std_total = np.std(total_counts)
        stability = 1.0 - (std_total / max(avg_total, 1))
        
        print(f"📈 총 객체 수 안정성:")
        print(f"  현재: {current_total}개")
        print(f"  평균: {avg_total:.1f}개")
        print(f"  표준편차: {std_total:.2f}")
        print(f"  안정성: {stability:.2f} ({'안정' if stability > 0.8 else '불안정'})")
    
    # 클래스별 상세 분석
    print(f"\n🏷️ 클래스별 개수 현황:")
    for class_name, count in current_counts.items():
        if count > 0:
            # 최근 히스토리에서 해당 클래스 분석
            class_history = []
            for entry in recent_counts:
                class_history.append(entry['classes'].get(class_name, 0))
            
            if class_history:
                avg_count = sum(class_history) / len(class_history)
                std_count = np.std(class_history)
                class_stability = 1.0 - (std_count / max(avg_count, 1))
                
                short_name = class_name.split('_')[0] if '_' in class_name else class_name
                status = "🟢" if class_stability > 0.8 else "🟡" if class_stability > 0.6 else "🔴"
                
                print(f"  {status} {short_name}: {count}개 (평균:{avg_count:.1f}, 안정성:{class_stability:.2f})")
    
    print(f"\n💡 추천사항:")
    if stability > 0.8:
        print("  ✅ 개수 파악이 안정적입니다. 현재 결과를 신뢰할 수 있습니다.")
    elif stability > 0.6:
        print("  🟡 개수가 약간 변동됩니다. 몇 초 더 관찰해보세요.")
    else:
        print("  ⚠️ 개수가 불안정합니다. 조명이나 카메라 각도를 조정해보세요.")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    improved_webcam_detection()