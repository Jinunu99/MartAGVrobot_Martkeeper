from collections import defaultdict, deque
from webcam.utils import calculate_iou, calculate_distance

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
        
        # 업데이트 횟수
        self.update_count = 0
        
    def update(self, current_detections):
        """새로운 프레임의 탐지 결과로 업데이트"""
        # 현재 탐지 결과를 히스토리에 추가
        self.detection_history.append(current_detections)
        self.update_count += 1
        
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
            'stability': stability_score,
            'update_count': self.update_count
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