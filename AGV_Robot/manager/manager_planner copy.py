from collections import deque
import sys
import os

# 상위 vision 폴더의 모듈들 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vision.path_planner import DirectionResolver

class ManagerPlanner:
    """
    관리자 로봇용 경로 계획 클래스
    순환 구조 제거, Detection 좌표에서만 Detection 실행
    """
    
    def __init__(self, position_map):
        self.position_map = position_map
        self.now_pos_x, self.now_pos_y = [6, 0]  # 초기 위치
        
        # Detection 가능한 매대 좌표들 (순환하지 않음)
        self.detection_coordinates = [
            [0, 1],  # [1,1] 매대 detection [0, 1], [0, 3], [0, 5]
            [0, 3],  # [1,3] 매대 detection  
            [0, 5],  # [1,5] 매대 detection
            [4, 5],  # [3,5] 매대 detection
            [4, 3],  # [3,3] 매대 detection
            [4, 1]   # [3,1] 매대 detection
        ]
        
        self.current_target = None    # 현재 목표 (수동 설정)
        self.middle_path = []         # 현재 경로
        
    def set_now_position(self, x, y):
        """현재 위치 설정"""
        self.now_pos_x = x
        self.now_pos_y = y
        
    def is_detection_point(self, x=None, y=None):
        """
        현재 위치가 Detection 가능한 좌표인지 확인
        
        Args:
            x, y: 확인할 좌표 (None이면 현재 위치 사용)
        
        Returns:
            bool: Detection 가능 여부
        """
        check_x = x if x is not None else self.now_pos_x
        check_y = y if y is not None else self.now_pos_y
        
        return [check_x, check_y] in self.detection_coordinates
        
    def get_detection_coordinates(self):
        """Detection 가능한 모든 좌표 반환"""
        return self.detection_coordinates.copy()
        
    def set_target(self, target_x, target_y):
        """수동으로 목표 설정"""
        self.current_target = [target_x, target_y]
        print(f"[ManagerPlanner] 목표 설정: ({target_x}, {target_y})")
        
    def get_current_target(self):
        """현재 목표 좌표 반환"""
        return self.current_target
        
    def clear_target(self):
        """목표 해제"""
        self.current_target = None
        print(f"[ManagerPlanner] 목표 해제")
        
    def bfs(self, target_x, target_y):
        """
        BFS 경로 탐색
        """
        print(f"[BFS] BFS 탐색 시작: 현재=({self.now_pos_x},{self.now_pos_y}) → 목표=({target_x},{target_y})")
        move = [[-1, 0], [0, 1], [1, 0], [0, -1]]   # AGV 이동방향 (상, 우, 하, 좌 순서로)
        
        n, m = len(self.position_map), len(self.position_map[0])
        visited = [[False]*m for _ in range(n)]
        prev = [[None]*m for _ in range(n)]
        queue = deque()

        # 현재의 위치를 방문처리
        sx, sy = self.now_pos_x, self.now_pos_y
        queue.append((sx, sy))
        visited[sx][sy] = True

        while queue:
            x, y = queue.popleft()

            if (x, y) == (target_x, target_y):
                path = []
                while (x, y) != (sx, sy):
                    path.append([x, y])
                    x, y = prev[x][y]
                path.append([sx, sy])
                path.reverse()
                return path

            for dx, dy in move:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and self.position_map[nx][ny] == 0:
                    if not visited[nx][ny]:
                        visited[nx][ny] = True
                        prev[nx][ny] = (x, y)
                        queue.append((nx, ny))
        
        return None

    def path_find_to_target(self):
        """
        현재 설정된 목표로 경로 계획
        """
        if not self.current_target:
            print(f"[ManagerPlanner] 목표가 설정되지 않음")
            return None
            
        target_x, target_y = self.current_target
        path = self.bfs(target_x, target_y)
        
        if path:
            self.middle_path = path
            print(f"[ManagerPlanner] 목표 ({target_x},{target_y})로 경로 생성: {len(path)}칸")
            return path
        else:
            print(f"[ManagerPlanner] 목표 ({target_x},{target_y})로 경로 생성 실패")
            return None
            
    def get_nearest_detection_point(self):
        """
        현재 위치에서 가장 가까운 Detection 포인트 찾기
        
        Returns:
            tuple: (좌표, 거리) 또는 None
        """
        if not self.detection_coordinates:
            return None
            
        min_distance = float('inf')
        nearest_point = None
        
        for point in self.detection_coordinates:
            # 맨하탄 거리 계산
            distance = abs(self.now_pos_x - point[0]) + abs(self.now_pos_y - point[1])
            if distance < min_distance:
                min_distance = distance
                nearest_point = point
                
        return (nearest_point, min_distance) if nearest_point else None
        
    def get_status(self):
        """
        현재 상태 정보 반환
        """
        return {
            'current_position': [self.now_pos_x, self.now_pos_y],
            'current_target': self.current_target,
            'is_at_detection_point': self.is_detection_point(),
            'detection_coordinates': self.detection_coordinates,
            'path_length': len(self.middle_path)
        }